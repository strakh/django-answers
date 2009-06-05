# -*- coding: utf-8 -*-
import types
import os
from cStringIO import StringIO
from PIL import Image
from django.db import models
from django.db.models import ImageField, FileField, IntegerField, CharField, TextField
from django.db.models import signals
from django.core.files.base import File
from django.dispatch import dispatcher
from django.utils.functional import curry
from django.db.models.fields.files import ImageField, ImageFieldFile
import tempfile

import md5 as hashclass
import uuid
from django.conf import settings

class Named(object):
    "Thing has a name, call it by its name then"
    def __unicode__(self):
        return self.name

class TooManyRelations(StandardError): pass

def HackishOneToOne(model, relatedName):
    class _DirtyLittleHack(object):
        def __get__(self, parent, type):
            if getattr(parent, '_related_cache', False):
                return parent._related_cache
            related = getattr(parent, '%s_set' % relatedName).all()
            if len(related) > 1:
                raise TooManyRelations, 'object %s has to many %s' % (parent, relatedName)
            elif len(related) == 0:
                return None
            
            parent._related_cache = related[0]
            return parent._related_cache
                   
    setattr(model, relatedName, _DirtyLittleHack())
    return models.ForeignKey(model, unique=True)

class BigIntegerField(IntegerField):
    def db_type(self):
        return 'bigint'

class PhotoFile(ImageFieldFile):
    def save(self, name, content, save=True):
        #image.save(dst_file, "JPEG", quality=settings.THUMBNAIL_QUALITY)
        
        super(PhotoFile, self).save(name, content, save)
        
    def clear_caches(self):
        dirname = os.path.dirname(self.name)
        basename = os.path.basename(self.name)
        name, _ = os.path.splitext(basename)
        for fname in self.storage.listdir(dirname)[1]:
            if fname != basename and fname.startswith(name):
                self.storage.delete(os.path.join(dirname,fname))
                
    def rotate(self, angle):
        orig = Image.open(self.storage.open(self.name))
        new = orig.rotate(angle)
        dst_file = tempfile.NamedTemporaryFile('rw+b')
        new.save(dst_file, orig.format)
        dst_file.seek(0)
        self.storage.delete(self.name)
        self.storage.save(self.name, File(dst_file))#we need a chunk'able django File
        self.clear_caches()
                    
    def photo_dimensions(self, width=None, height=None, crop=None):
        if crop is None:
            try:
                # si no esta seteada el area de crop, tomar el tamaño de la imagen de la base
                src_w, src_h = self.width, self.height
            except ValueError:#No hay imagen asignada, mas adelante usaremos las dimensiones default
                src_w = src_h = None
        else:
            # tomar el tamaño del area de crop
            src_w, src_h = crop[2:]

        if src_w is None or src_h is None:
            # si las dimensiones originales no estan seteadas -> uso las de la foto default
            src_w, src_h = self.field.default_photo_dimensions

        if width is None and height is None:
            # si no piden ningun resize, devuelvo los valores anteriores
            return src_w, src_h
        else:
            if width is not None and height is not None:
                # si los dos tienen valor -> fit
                return self._fit((src_w, src_h), (width, height))
            else:
                # uno solo tiene valor -> calcular el otro
                return self._scale((src_w, src_h), (width, height))

    def photo_url(self, width=None, height=None, crop=None, crop_name=None):
        filename = self.name or self.field.default_photo
           
        if crop is None and height is None and width is None:
            # si me estan pidiendo la imagen original, devuelvo la imagen original
            return self.storage.url(filename)
        try:
            dot_index = filename.rindex('.')
            path, ext = filename[:dot_index], filename[dot_index:]
        except ValueError: # filename has no dot
            path, ext = filename, ""
        
        if crop is not None:
            assert crop_name is not None
            path += "_%s@%d+%d+%dx%d" % ((crop_name,)+crop)
        
        if width is not None or height is not None:
            dimensions = self.photo_dimensions(crop=crop, width=width, height=height)
            if dimensions is None:
                return None
            width, height = dimensions
            path += "_%dx%d" % (width, height)
        
        if not self.storage.exists(path+ext):
            self._mkthumb(filename, path+ext, crop, width, height)
        
        return self.storage.url(path+ext)    
        
    def _mkthumb(self, src, dst, crop, width, height):
        src_file = self.storage.open(src)
        image = Image.open(src_file)
        
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        if crop is not None:
            x, y, w, h = crop
            image = image.crop((x, y, x+w, y+h))
        
        if width is not None and height is not None:
            if crop is not None and width == crop[2] and height == crop[3]:
                pass
            else:
                image = image.resize((width, height), Image.ANTIALIAS)
        
        dst_file = tempfile.NamedTemporaryFile('rw+b')
        image.save(dst_file, "JPEG", quality=settings.THUMBNAIL_QUALITY)
        dst_file.seek(0)
        self.storage.save(dst, File(dst_file))#we need a chunk'able django File
        
    @staticmethod
    def _fit((src_w, src_h), (dst_w, dst_h)):
        """inspirado en pygame.Rect.fit:
        Returns a new rectangle that is resized to fit another.
        The aspect ratio of the original Rect is preserved, so the new rectangle may be smaller than the target in either width or height. 
        """
        xratio = float(src_w) / float(dst_w)
        yratio = float(src_h) / float(dst_h)
        maxratio = max(xratio, yratio)
        w = int(src_w / maxratio + .5)
        h = int(src_h / maxratio + .5)
        return (w, h)
    
    @staticmethod
    def _scale((src_w, src_h), (dst_w, dst_h)):
        """ calcular el valor que falta a partir del otro """
        if dst_w is None:
            dst_w = int(dst_h/float(src_h)*src_w + .5)
        if dst_h is None:
            dst_h = int(dst_w/float(src_w)*src_h + .5)
        return (dst_w, dst_h)

class PhotoField(ImageField):
    attr_class = PhotoFile
    
    def __init__(self, default_photo=None, default_photo_dimensions=(100, 100), *a, **kw):
        default_photo = default_photo or settings.DEFAULT_PICTURE_FILE
        super(PhotoField, self).__init__(*a, **kw)
        self.default_photo = default_photo
        self.default_photo_dimensions = default_photo_dimensions
        
        def generate_filename(this, filename):
            hash = str(uuid.uuid4())
            try:
                dot_index = filename.rindex('.')
                filename = hash + filename[dot_index:]
            except ValueError: # filename has no dot
                filename = hash
            return os.path.join(self.get_directory_name(), *[hash[n] for n in range(settings.IMAGE_BUCKET_DEPTH)] + [filename])
        self.generate_filename = generate_filename

class PhotoCrop(object):
    def __init__(self, instance, field, value, ratio=None):
        self.instance = instance
        self.field = field
        self._value = value
        self.ratio = ratio
        
    def as_tuple(self):
        tup = eval(self._value)
        if not isinstance(tup, tuple):
            raise ValueError("how come, value was not a tuple")
        return tup
    
    @staticmethod
    def crop_from_string(string):
        return tuple(map(int, string.strip("()").split(",")))
    
    def photo_url(self, width=None, height=None):
        crop = self.crop_from_string(self._value)
        return getattr(self.instance, self.field.source_field).photo_url(crop_name=self.field.attname, crop=crop, width=width, height=height)

    def photo_dimensions(self, width=None, height=None):
        crop = self.crop_from_string(self._value)
        return getattr(self.instance, self.field.source_field).photo_dimensions(crop=crop, width=width, height=height)

    def validate_ratio(self, crop):
        if not self.field.ratio:
            return crop
        x,y,w,h = crop
        return x,y,w,int(w*self.field.ratio)
    
    def __getstate__(self):
        # We only need the actual string value pickled
        return {'_value': self._value}
    
    def __unicode__(self):
        return unicode(self._value)

class CropDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError, "%s can only be accessed from %s instances." % (self.field.name(self.owner.__name__))
        value = instance.__dict__[self.field.name]
        if not isinstance(value, PhotoCrop):
            # Create a new instance of FieldFile, based on a given file name
            instance.__dict__[self.field.name] = PhotoCrop(instance, self.field, value, self.field.ratio)
        elif not hasattr(value, 'field'):
            # The CropField was pickled, so some attributes need to be reset.
            value.instance = instance
            value.field = self.field
            
        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value

class PhotoCropField(TextField):
    def __init__(self, source_field=None, default="(0,0,100,100)", ratio=None, *a, **kw):
        super(PhotoCropField, self).__init__(default=default, *a, **kw)
        self.source_field = source_field
        self.ratio = ratio
    
    def get_db_prep_lookup(self, lookup_type, value):
        if hasattr(value, '_value'):
            value = value._value
        return super(FileField, self).get_db_prep_lookup(lookup_type, value)

    def get_db_prep_value(self, value):
        "Returns field's value prepared for saving into a database."
        # Need to convert Crop objects provided via a form to unicode for database insertion
        if value is None:
            return None
        if hasattr(value, '_value'):
            value = value._value
        return unicode(value)
    
    def contribute_to_class(self, cls, name):
        super(PhotoCropField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, CropDescriptor(self))
