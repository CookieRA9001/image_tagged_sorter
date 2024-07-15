import os
import sys
import json
import shutil 
import subprocess
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.lang import Builder

if not os.path.exists("objects"):
    print("KV Object Dir is missing! Terrminating script")
    sys.exit()

Builder.load_file('objects/Tab.kv')
Builder.load_file('objects/TagPopup.kv')
Builder.load_file('objects/AddedTag.kv')
Builder.load_file('objects/TagSelect.kv')
Builder.load_file('objects/SearchedImage.kv')
Builder.load_file('objects/PalletImage.kv')
Builder.load_file('objects/Base.kv')
Builder.load_file('objects/TaggingPage.kv')
Builder.load_file('objects/SearchPage.kv')
Builder.load_file('objects/PalletPage.kv')

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
if not os.path.exists("database/pallet"):
    os.makedirs("database/pallet")

TAGS = json.load(open('database/tags.json'))["tags"]
TAGS = [t.lower() for t in TAGS]
TAGGED_IMAGES = {}
IMAGES = []
PATH = os.getcwd()+"\\database\\images\\"
PALLET = []
# to-do: load pallet from pallet folder
for file in os.listdir("database\pallet"):
    filename = os.fsdecode(file)
    PALLET.append(filename)
print(PALLET)

for i in TAGS:
    if not os.path.exists("database/taggedFiles/" + i + ".json"):
        with open("database/taggedFiles/" + i + ".json", 'w') as file: 
            file.write("{\"images\": []}")
    TAGGED_IMAGES[i] = json.load(open("database/taggedFiles/" + i + ".json"))["images"]

    for img in TAGGED_IMAGES[i]:
        IMAGES.append(img)
    IMAGES = list(set(IMAGES))

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
        self.tagSelects = [None, None, None]
        self.selectedTags = []
        self.savedSearchText = ""
        self.selectedImages = []
        self.currentImageIndex = -1
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
        self.addedTagBox.clear_widgets()
        self.selectedTags = []
        self.searchTags()

class SearchedImage(Widget):
    searchPage = None

    def __init__(self, page, **kwargs):
        self.searchPage = page
        super().__init__(**kwargs)

    def addToPallet(self):
        img = os.path.basename(self.img.source)
        if not img in PALLET:
            PALLET.append(img)
            self.searchPage.searchForImages()
            shutil.copy(self.img.source, "database/pallet/" + img)

class SearchPage(Widget):
    filterTags = [] # "and" search
    searchText = ""
    tagSearchText = ""
    loadedImage = []
    tagSelects = [None, None, None]

    def build(self):
        self.imageList1.bind(minimum_height=self.imageList1.setter('height'))
        self.imageList2.bind(minimum_height=self.imageList2.setter('height'))
        self.imageList3.bind(minimum_height=self.imageList3.setter('height'))
        self.tagSelects = [None, None, None]
        self.clearFilters()

    def searchForImages(self):
        self.loadedImage = []

        if len(self.filterTags) == 0:
            # to-do: remove the images that are in the pallet
            temp = [i for i in IMAGES if self.searchText in i and not i in PALLET]
            for i in range(0, min(100, len(temp))):
                self.loadedImage.append(temp[i])

        else:
            # to-do: remove the images that are in the pallet
            temp = TAGGED_IMAGES[self.filterTags[0]].copy()
            for tag in self.filterTags:
                temp = list(set(temp).intersection(TAGGED_IMAGES[tag])) # brute force
            
            temp = [i for i in temp if self.searchText in i and not i in PALLET]
            for i in range(0, min(100, len(temp))):
                self.loadedImage.append(temp[i])

        self.loadImages()
    
    def loadImages(self):
        index = 1
        self.imageList1.clear_widgets()
        self.imageList2.clear_widgets()
        self.imageList3.clear_widgets()
        for img in self.loadedImage:
            loaded_img = SearchedImage(self)
            loaded_img.img.source = PATH + img
            if index == 1:
                self.imageList1.add_widget(loaded_img)
            elif index == 2:
                self.imageList2.add_widget(loaded_img)
            elif index == 3:
                self.imageList3.add_widget(loaded_img)
            index += 1
            if index == 4:
                index = 1

    def searchByName(self, text = searchText):
        self.searchText = text
        self.searchForImages()

    def clearFilters(self):
        self.searchInput.text = ""
        self.searchTagInput.text = ""
        self.filterTags = []
        self.searchText = ""
        self.tagSearchText = ""
        self.addedTagBox.clear_widgets()
        self.searchTags()
        self.searchForImages()

    def searchTags(self, text = tagSearchText):
        self.tagSearchText = text
        res = [i for i in TAGS if text in i and not i in self.filterTags] # Very inefficiant
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

    def addTag(self, tag):
        if tag in self.filterTags: 
            return
        addedTag = AddedTag(self)
        addedTag.setName(tag)
        self.addedTagBox.add_widget(addedTag)
        self.filterTags.append(tag)
        self.searchForImages()

    def removeTag(self, tag):
        self.filterTags.remove(tag)
        self.searchForImages()

class PalletImage(Widget):
    palletPage = None
    selectedImageElement = None

    def __init__(self, page, **kwargs):
        self.palletPage = page
        super().__init__(**kwargs)

    def removeFromPallet(self):
        img = os.path.basename(self.img.source)
        if img in PALLET:
            PALLET.remove(img)
            self.palletPage.loadImages()
            os.remove("database/pallet/" + img) 

    def selectImage(self):
        self.palletPage.fullImageView.source = self.img.source

class PalletPage(Widget):
    def build(self):
        self.imageList1.bind(minimum_height=self.imageList1.setter('height'))
        self.imageList2.bind(minimum_height=self.imageList2.setter('height'))
        self.imageList3.bind(minimum_height=self.imageList3.setter('height'))
        self.loadImages()

    def loadImages(self):
        index = 1
        self.imageList1.clear_widgets()
        self.imageList2.clear_widgets()
        self.imageList3.clear_widgets()
        for img in PALLET:
            loaded_img = PalletImage(self)
            loaded_img.img.source = PATH + img
            if index == 1:
                self.imageList1.add_widget(loaded_img)
            elif index == 2:
                self.imageList2.add_widget(loaded_img)
            elif index == 3:
                self.imageList3.add_widget(loaded_img)
            index += 1
            if index == 4:
                index = 1

    def openPalletFolder(self):
        subprocess.Popen(r'explorer "' + os.getcwd()+"\\database\\pallet\\")

class Tab(Button):
    base = None

    def __init__(self, base, **kwargs):
        super().__init__(**kwargs)
        self.base = base

    def switchToTab(self):
        match self.text:
            case "Tagging":
                self.base.openTaggingPage()
                pass
            case "Search":
                self.base.openSearchPage()
                pass
            case "Pallet":
                self.base.openPalletPage()
                pass

class Base(Widget):
    openPage = None
    currentPageName = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        taggingTab = Tab(self)
        taggingTab.text = "Tagging"
        searchTab = Tab(self)
        searchTab.text = "Search"
        palletTab = Tab(self)
        palletTab.text = "Pallet"
        self.tabPanel.add_widget(taggingTab)
        self.tabPanel.add_widget(searchTab)
        self.tabPanel.add_widget(palletTab)

    def openTaggingPage(self):
        if self.currentPageName == "Tagging":
            return
        if not self.openPage == None:
            self.tab.remove_widget(self.openPage)
        
        tp = TaggingPage()
        self.tab.add_widget(tp)
        self.openPage = tp
        tp.build()
        self.currentPageName = "Tagging"

    def openSearchPage(self):
        if self.currentPageName == "Search":
            return
        if not self.openPage == None:
            self.tab.remove_widget(self.openPage)
        
        sp = SearchPage()
        self.tab.add_widget(sp)
        self.openPage = sp
        sp.build()
        self.currentPageName = "Search"

    def openPalletPage(self):
        if self.currentPageName == "Pallet":
            return
        if not self.openPage == None:
            self.tab.remove_widget(self.openPage)
        
        pp = PalletPage()
        self.tab.add_widget(pp)
        self.openPage = pp
        pp.build()
        self.currentPageName = "Pallet"

class ImageSorterApp(App):
    def build(self):
        base = Base()
        base.openTaggingPage()
        return base

if __name__ == "__main__":
    ImageSorterApp().run()

    