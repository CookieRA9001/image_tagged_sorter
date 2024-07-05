import os
import sys
import json
import shutil 
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
#from kivy.properties import ObjectProperty
from kivy.lang import Builder

if not os.path.exists("objects"):
    print("KV Object Dir is missing! Terrminating script")
    sys.exit()

Builder.load_file('objects/TagPopup.kv')
Builder.load_file('objects/AddedTag.kv')
Builder.load_file('objects/TagSelect.kv')
Builder.load_file('objects/Base.kv')
Builder.load_file('objects/TaggingPage.kv')

## INIT DIR
if not os.path.exists("database"):
    os.makedirs("database")
if not os.path.exists("database/tags.json"): 
    with open("database/tags.json", 'w') as file: 
        file.write("{\"tags\": []}")
if not os.path.exists("database/taggedFiles"):
    os.makedirs("database/taggedFiles")
if not os.path.exists("database/images"):
    os.makedirs("database/images")

TAGS = json.load(open('database/tags.json'))["tags"]
TAGS = [t.lower() for t in TAGS]

for i in TAGS:
    if not os.path.exists("database/taggedFiles/" + i + ".json"):
        with open("database/taggedFiles/" + i + ".json", 'w') as file: 
            file.write("{\"images\": []}")

class TagPopup(Popup):
    taggingPage = None

    def __init__(self, tp, **kwargs):
        self.taggingPage = tp
        super().__init__(**kwargs)

    def addtag(self, text):
        text = text.lower()
        
        if not text in TAGS: 
            with open("database/taggedFiles/" + text + ".json", 'w') as file: 
                file.write("{\"images\": []}")
            TAGS.append(text)
            with open("database/tags.json", "w") as f:
                json.dump({"tags": TAGS}, f)

        self.taggingPage.addTag(text)
        self.dismiss()

class TagSelect(Button):
    taggingPage = None

    def __init__(self, tp, **kwargs):
        super().__init__(**kwargs)
        self.taggingPage = tp
        self.bind(on_press=self.addTag)

    def addTag(self, obj):
        print(self.text)
        self.taggingPage.addTag(self.text)
        self.taggingPage.searchTags()

class AddedTag(Widget):
    taggingPage = None

    def __init__(self, tp, **kwargs):
        self.taggingPage = tp
        super().__init__(**kwargs)

    def setName(self, name):
        self.tagName = name
        self.textWidth = len(name)*13
    
    def removeSelf(self):
        self.taggingPage.removeTag(self.tagName)
        self.taggingPage.addedTagBox.remove_widget(self)
        self.taggingPage.searchTags()

class TaggingPage(Widget):
    tagSelects = [None, None, None]
    selectedTags = []
    savedSearchText = ""
    selectedImages = []
    currentImageIndex = -1

    def build(self):
        self.tagSelects[0] = TagSelect(self)
        self.tagSelects[1] = TagSelect(self)
        self.tagSelects[2] = TagSelect(self)
        
        self.tagBox.add_widget(self.tagSelects[0])
        self.tagBox.add_widget(self.tagSelects[1])
        self.tagBox.add_widget(self.tagSelects[2])
        
        self.updateTagSelects(TAGS)

    def searchTags(self, text = savedSearchText):
        self.savedSearchText = text
        res = [i for i in TAGS if text in i and not i in self.selectedTags] # Very inefficiant
        self.updateTagSelects(res)
    
    def updateTagSelects(self, tags):
        self.updateTagSelect(0, tags)
        self.updateTagSelect(1, tags)
        self.updateTagSelect(2, tags)
    
    def updateTagSelect(self, index, tags):
        if len(tags) > index:
            if self.tagSelects[index] == None:
                self.tagSelects[index] = TagSelect(self)
                self.tagBox.add_widget(self.tagSelects[index])
            self.tagSelects[index].text = tags[index]
            
        elif not self.tagSelects[index] == None:
            self.tagBox.remove_widget(self.tagSelects[index])
            self.tagSelects[index] = None
        
    def openAddTagPopup(self):
        TagPopup(self).open()

    def addTag(self, tag):
        if tag in self.selectedTags: 
            return
        addedTag = AddedTag(self)
        addedTag.setName(tag)
        self.addedTagBox.add_widget(addedTag)
        self.selectedTags.append(tag)
    
    def removeTag(self, tag):
        self.selectedTags.remove(tag)

    def saveTaggedImage(self):
        if self.currentImageIndex == -1:
            return
        
        # change directory to script root
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)
        new_file_name = self.imageNameInput.text

        if os.path.exists("database/images/" + new_file_name):
            self.imageNameInput.foreground_color = (1,0,0,1)
            return

        shutil.copy(self.currentImage.source, "database/images/" + new_file_name)
        
        for tag in self.selectedTags:
            # soruce: https://www.geeksforgeeks.org/append-to-json-file-using-python/
            with open('database/taggedFiles/' + tag + ".json",'r+') as file:
                file_data = json.load(file)
                file_data["images"].append(new_file_name)
                file.seek(0)
                json.dump(file_data, file)

        self.nextImage()
        self.imageNameInput.foreground_color = (0,0,0,1)

    # TO-DO: switch to this?: https://kivymd.readthedocs.io/en/0.104.0/components/file-manager/index.html
    def openImageSelect(self):
        from plyer import filechooser
        # would be nice to add "image only but cant find how to do it (to lazy)"
        filechooser.open_file(on_selection = self.selected, multiple=True)
        
    def selected(self, selection):
        self.selectedImages = selection
        self.currentImageIndex = -1
        self.imageBoxBtn.text = ""
        self.nextImage()
    
    def nextImage(self):
        self.currentImageIndex += 1
        self.resetImageTags()

        if self.currentImageIndex >= len(self.selectedImages):
            self.outOfImages()
            return
        
        self.currentImage.source = self.selectedImages[self.currentImageIndex]
        name = os.path.basename(self.selectedImages[self.currentImageIndex])
        self.imageNameInput.text = name

    def outOfImages(self):
        self.imageBoxBtn.text = "Click me to select image/s"
        self.selectedImages = []
        self.imageNameInput.text = ""
        self.currentImage.source = ""
        self.currentImageIndex = -1
    
    def resetImageTags(self):
        tags = [i for i in self.addedTagBox.children]
        for tag in tags:
            if isinstance(tag, AddedTag):
                self.addedTagBox.remove_widget(tag)
        self.selectedTags = []
        self.searchTags()

class Base(Widget):
    pass

class ImageSorterApp(App):
    def build(self):
        base = Base()
        tp = TaggingPage()
        base.tab.add_widget(tp)
        tp.build()
        return base

if __name__ == "__main__":
    ImageSorterApp().run()

    