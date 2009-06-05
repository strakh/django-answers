import re
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class TaggedItem(models.Model):
    """A tag on an item."""
    tag = models.CharField(max_length = 50)
    tagging_content_type = models.ForeignKey(ContentType, related_name='tagging_ctype_set')
    tagging_object_id = models.PositiveIntegerField()
    tagging_instance = generic.GenericForeignKey(ct_field="tagging_content_type", fk_field="tagging_object_id")
    
    tagged_content_type = models.ForeignKey(ContentType, related_name='tagged_ctype_set')
    tagged_object_id = models.PositiveIntegerField()
    tagged_instance = generic.GenericForeignKey(ct_field="tagged_content_type", fk_field="tagged_object_id")    

    class Meta:
        ordering = ["tag"]
        app_label = 'woozp'

    def __unicode__(self):
        return self.tag

class Taggeable(models.Model):
    class Meta:
        abstract = True
        
    tags_text = models.CharField(max_length=255, null=True, blank=True)
    tags = generic.GenericRelation(TaggedItem, object_id_field="tagging_content_type_id", content_type_field="tagging_object_id")
    
    def save(self):
        super(Taggeable, self).save()
        self.update_tags()
    
    def update_tags(self):
        if not self.tags_text:
            return
        regex = re.compile('(\(\ *(.*?)\ *\:\ *(\d*?)\ *\))', re.I)
        ids = regex.findall(self.tags_text)
        if not ids:
            return
        
        own_ctype = ContentType.objects.get_for_model(self)
        TaggedItem.objects.filter(tagging_object_id=self.id, tagging_content_type = own_ctype).delete()
        for tag, content_type, object_id in ids:
            c_type = ContentType.objects.get(name=content_type)
            TaggedItem(tagging_instance=self, tagged_object_id=int(object_id),
                       tagged_content_type=c_type, tag=tag).save()
        
