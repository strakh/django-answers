import os

def recursive_link(base_from, base_to, exclude_dirs=[".svn"]):
    for root, dirs, files in os.walk(base_from):
        new_path = root[len(base_from):]
        path_to = os.path.join( base_to, new_path )
        if not os.path.isdir(path_to):
            os.makedirs(path_to)
        for name in files:
            file_to = os.path.join(path_to, name)
            if os.path.isfile(file_to):
                os.unlink(file_to)
            file_from = os.path.join(root, name)
            os.link(file_from, file_to)
        for d in exclude_dirs:
            if d in dirs:
                dirs.remove(d)  # don't visit SVN directories

if __name__ == "__main__":
    pass
    #base_from = "woozp/models/fixtures/images/"
    #base_to = "other/directory"
    #recursive_symlink(base_from, base_to)
