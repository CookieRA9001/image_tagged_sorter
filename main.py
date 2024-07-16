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
Builder.load_file('objects/FullImagePopup.kv')
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
IMAGE_TAGS = {}
IMAGES = []
PATH = os.getcwd()+"\\database\\images\\"
PALLET = []
for file in os.listdir("database\pallet"):
    filename = os.fsdecode(file)
    PALLET.append(filename)

for i in TAGS:
    if not os.path.exists("database/taggedFiles/" + i + ".json"):
        with open("database/taggedFiles/" + i + ".json", 'w') as file: 
            file.write("{\"images\": []}")
    else:
        # clean up
        with open("database/taggedFiles/" + i + ".json", 'r+') as file: 
            file_data = json.load(file)
            file_data["images"] = list(set(file_data["images"]))
            file_data["images"] = [x for x in file_data["images"] if os.path.exists("database/images/" + x)]
            file.seek(0)
            json.dump(file_data, file)
            file.truncate()

    TAGGED_IMAGES[i] = json.load(open("database/taggedFiles/" + i + ".json"))["images"]

    for img in TAGGED_IMAGES[i]:
        if not img in IMAGE_TAGS.keys():
            IMAGE_TAGS[img] = []
        IMAGE_TAGS[img].append(i)
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

    def addTag(self, obj = None):
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

    def searchTags(self, text = None):
        if text == None:
            text = self.savedSearchText
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

    def saveTaggedImage(self, editFile = False):
        if self.currentImageIndex == -1:
            return
        
        # change directory to script root
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)
        old_file_name = os.path.basename(self.currentImage.source)
        new_file_name = self.imageNameInput.text
        renameFile = False
        
        if editFile and not new_file_name == old_file_name:
            renameFile = True

        if (not editFile or renameFile) and os.path.exists("database/images/" + new_file_name):
            self.imageNameInput.foreground_color = (1,0,0,1)
            return

        if not editFile or renameFile:
            shutil.copy(self.currentImage.source, "database/images/" + new_file_name)
        if renameFile:
            os.remove("database/images/" + old_file_name) 
        
        if editFile:
            IMAGE_TAGS.pop(old_file_name)
            IMAGES.remove(old_file_name)
        IMAGE_TAGS[new_file_name] = []
        IMAGES.append(new_file_name)

        for tag in self.selectedTags:
            if editFile and old_file_name in TAGGED_IMAGES[tag]:
                TAGGED_IMAGES[tag].remove(old_file_name)
            TAGGED_IMAGES[tag].append(new_file_name)
            IMAGE_TAGS[new_file_name].append(tag)
            # soruce: https://www.geeksforgeeks.org/append-to-json-file-using-python/
            with open('database/taggedFiles/' + tag + ".json",'r+') as file:
                file_data = json.load(file)
                if editFile and old_file_name in file_data["images"]:
                    file_data["images"].remove(old_file_name)
                file_data["images"].append(new_file_name)
                file.seek(0)
                json.dump(file_data, file)
                file.truncate()

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
        self.searchTagInput.text = ""

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

    def openImageFullView(self):
        FullImagePopup(self).open()

class FullImagePopup(Popup):
    searchImage = None
    taggingPage = None

    def __init__(self, image, **kwargs):
        super().__init__(**kwargs)
        taggingPage = TaggingPage()
        self.add_widget(taggingPage)
        taggingPage.build()
        self.searchImage = image
        self.taggingPage = taggingPage

        # prepare tagging page in popup
        taggingPage.imageBoxBtn.text = ""
        taggingPage.imageBoxBtn.disabled = True
        taggingPage.currentImage.source = image.img.source
        taggingPage.nextBtn.text = "Save"
        taggingPage.nextBtn.bind(on_release=self.saveAndClose)
        taggingPage.currentImageIndex = 0

        # load image data
        taggingPage.selectedImages = [image.img.source]
        taggingPage.currentImage.source = taggingPage.selectedImages[0]
        name = os.path.basename(taggingPage.selectedImages[0])
        taggingPage.imageNameInput.text = name

        for tag in IMAGE_TAGS[name]:
            taggingPage.addTag(tag)

        taggingPage.searchTags()


    def saveAndClose(self, obj = None):
        self.taggingPage.saveTaggedImage(True)
        self.searchImage.searchPage.searchForImages()
        self.dismiss()

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
        il1_height = 0
        il2_height = 0
        il3_height = 0
        for img in self.loadedImage:
            loaded_img = SearchedImage(self)
            loaded_img.img.source = PATH + img
            img_height = 1/loaded_img.img.image_ratio
            min_height = min(il1_height,il2_height,il3_height)
            if min_height == il1_height:
                il1_height += img_height
                self.imageList1.add_widget(loaded_img)
            elif min_height == il2_height:
                il2_height += img_height
                self.imageList2.add_widget(loaded_img)
            elif min_height == il3_height:
                il3_height += img_height
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
        self.palletPage.fullImageName.text = os.path.basename(self.img.source)

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
        il1_height = 0
        il2_height = 0
        il3_height = 0
        for img in PALLET:
            loaded_img = PalletImage(self)
            loaded_img.img.source = PATH + img
            img_height = 1/loaded_img.img.image_ratio
            min_height = min(il1_height,il2_height,il3_height)
            if min_height == il1_height:
                il1_height += img_height
                self.imageList1.add_widget(loaded_img)
            elif min_height == il2_height:
                il2_height += img_height
                self.imageList2.add_widget(loaded_img)
            elif min_height == il3_height:
                il3_height += img_height
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

    