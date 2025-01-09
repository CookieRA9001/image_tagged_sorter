import os
import sys
import json
import shutil 
import subprocess
import uuid
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.clock import Clock
from functools import partial
from kivy.config import Config

CONFIG_SEARCHVIEW_IMAGE_COUNT = 100
CONFIG_UPDATE_SPEED = 60.0
CONFIG_TAG_SEARCH_COUNT = 20
CONFIG_SCROLL_SPEED = 60
CONFIG_AUTO_TAG_UNTAGGED_IMAGES = True

Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')

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
if not os.path.exists("database/categories.json"): 
    with open("database/categories.json", 'w') as file: 
        file.write("{\"categories\": {}}")
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
CATEGORIES = json.load(open('database/categories.json'))["categories"]
PATH = os.getcwd()+"\\database\\images\\"
PALLET = []
SEARCH_BLACKLIST = []
UPDATE_QUEUE = []

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
            json.dump(file_data, file, indent=2)
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
            goToRoot()
            with open("database/taggedFiles/" + text + ".json", 'w') as file: 
                file.write("{\"images\": []}")
            TAGS.append(text)
            with open("database/tags.json", "w") as f:
                json.dump({"tags": TAGS}, f, indent=2)
            TAGGED_IMAGES[text] = []

        self.taggingPage.addTag(text)
        self.dismiss()

class TagSelect(Button):
    taggingPage = None
    tagName = ""

    def __init__(self, tp, **kwargs):
        super().__init__(**kwargs)
        self.taggingPage = tp
        self.bind(on_press=self.addTag)
    
    def setTag(self, tag):
        self.tagName = tag
        self.text = tag + " [" + str(len(TAGGED_IMAGES[tag])) + "]"

    def addTag(self, obj = None):
        self.taggingPage.addTag(self.tagName)
        self.taggingPage.searchTags()

class AddedTag(Widget):
    taggingPage = None

    def __init__(self, tp, **kwargs):
        self.taggingPage = tp
        super().__init__(**kwargs)

    def setName(self, name):
        self.tagName = name
        self.textWidth = len(name)*7
    
    def removeSelf(self):
        self.taggingPage.removeTag(self.tagName)
        self.taggingPage.addedTagBox.remove_widget(self)
        self.taggingPage.searchTags()

class TaggingPage(Widget):
    tagSelects = []
    selectedTags = []
    savedSearchText = ""
    selectedImages = []
    currentImageIndex = -1

    def build(self):
        self.tagSelects = []
        self.selectedTags = []
        self.savedSearchText = ""
        self.selectedImages = []
        self.currentImageIndex = -1

        self.tagBox.bind(minimum_height=self.tagBox.setter('height'))
        self.addedTagBox.bind(minimum_height=self.addedTagBox.setter('height'))

        self.updateTagSelects(TAGS)

    def searchTags(self, text = None):
        if text == None:
            text = self.savedSearchText
        res = []
        self.savedSearchText = text
        if len(text)>0 and text[0] == '@':
            cat_text = text[1:]
            cats = [c for c in CATEGORIES if cat_text in c]
            res = set(())
            for c in cats:
                for t in CATEGORIES[c]:
                    res.add(t)
            res = list(res)
            res = [i for i in res if not i in self.selectedTags]
        else:
            res = [i for i in TAGS if text in i and not i in self.selectedTags] # Very inefficiant
        self.updateTagSelects(res)
    
    def updateTagSelects(self, tags):
        for tagSelect in self.tagSelects:
            self.tagBox.remove_widget(tagSelect)

        for i in range(0, min(len(tags), CONFIG_TAG_SEARCH_COUNT)):
            self.tagSelects.append(TagSelect(self))
            self.tagBox.add_widget(self.tagSelects[i])
            self.tagSelects[i].setTag(tags[i])    
        
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

    def skipImage(self):
        if self.currentImageIndex == -1:
            return
        
        self.nextImage()
        self.imageNameInput.foreground_color = (0,0,0,1)

    def saveTaggedImage(self, editFile = False):
        global IMAGES, IMAGE_TAGS, TAGGED_IMAGES

        if self.currentImageIndex == -1:
            return
        
        goToRoot()
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
            # clear old data from data lists and json files
            for tag in IMAGE_TAGS[old_file_name]:
                TAGGED_IMAGES[tag].remove(old_file_name)
                
                if tag in self.selectedTags:
                    continue

                with open('database/taggedFiles/' + tag + ".json",'r+') as file:
                    file_data = json.load(file)
                    if old_file_name in file_data["images"]:
                        file_data["images"].remove(old_file_name)
                    file.seek(0)
                    json.dump(file_data, file, indent=2)
                    file.truncate()      

            IMAGE_TAGS.pop(old_file_name)
            IMAGES.remove(old_file_name)
        
        IMAGE_TAGS[new_file_name] = []
        IMAGES.append(new_file_name)

        if CONFIG_AUTO_TAG_UNTAGGED_IMAGES and len(self.selectedTags) == 0:
            self.selectedTags.append("untagged")

        for tag in self.selectedTags:
            TAGGED_IMAGES[tag].append(new_file_name)
            IMAGE_TAGS[new_file_name].append(tag)
            # soruce: https://www.geeksforgeeks.org/append-to-json-file-using-python/
            with open('database/taggedFiles/' + tag + ".json",'r+') as file:
                file_data = json.load(file)
                if editFile and old_file_name in file_data["images"]:
                    file_data["images"].remove(old_file_name)
                file_data["images"].append(new_file_name)
                file.seek(0)
                json.dump(file_data, file, indent=2)
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
    myColumn = 0

    def __init__(self, page, **kwargs):
        self.searchPage = page
        super().__init__(**kwargs)

    def addToPallet(self):
        img = os.path.basename(self.img.source)
        self.removeSelfFromList()
        if not img in PALLET:
            PALLET.append(img)
            #self.searchPage.searchForImages()
            shutil.copy(self.img.source, "database/pallet/" + img)
    
    def removeFromSearch(self):
        img = os.path.basename(self.img.source)
        SEARCH_BLACKLIST.append(img)
        #self.searchPage.searchForImages()
        self.searchPage.updateBlacklist()
        self.removeSelfFromList()

    def openImageFullView(self):
        FullImagePopup(self).open()
    
    def removeSelfFromList(self):
        self.parent.remove_widget(self)
        img_height = 1/self.img.image_ratio
        match self.myColumn:
            case 1:
                self.searchPage.il1_height -= img_height
            case 2:
                self.searchPage.il2_height -= img_height
            case 3:
                self.searchPage.il3_height -= img_height
            case _:
                print("Error: missing column number!")

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
        taggingPage.botBtnGrid.remove_widget(taggingPage.skipBtn)

        # load image data
        taggingPage.selectedImages = [image.img.source]
        taggingPage.currentImage.source = taggingPage.selectedImages[0]
        name = os.path.basename(taggingPage.selectedImages[0])
        taggingPage.imageNameInput.text = name

        for tag in IMAGE_TAGS[name]:
            taggingPage.addTag(tag)

        taggingPage.searchTags()

    def saveAndClose(self, obj = None):
        name = os.path.basename(self.taggingPage.selectedImages[0])

        self.taggingPage.saveTaggedImage(True)
        self.dismiss()

        # check if it still applies to the filter
        # to-do: update when adding more filtering options
        filtered = False
        if len(self.searchImage.searchPage.filterTags) != 0:
            filteredSet = set(self.searchImage.searchPage.filterTags)
            if not self.searchImage.searchPage.tagBlackListMode:
                filtered = True
                for tag in IMAGE_TAGS[name]:
                    if tag in filteredSet:
                        filtered = False
                        break
            else: # select only the images that dont have the tags
                for tag in IMAGE_TAGS[name]:
                    if tag in filteredSet:
                        filtered = True
                        break

        # if not, remove it
        if (not filtered): return
        
        self.searchImage.removeSelfFromList()

class SearchPage(Widget):
    filterTags = [] # "and" search
    searchText = ""
    tagSearchText = ""
    loadedImage = []
    tagSelects = []
    il1_height = 0
    il2_height = 0
    il3_height = 0
    tagBlackListMode = False

    def build(self):
        self.imageList1.bind(minimum_height=self.imageList1.setter('height'))
        self.imageList2.bind(minimum_height=self.imageList2.setter('height'))
        self.imageList3.bind(minimum_height=self.imageList3.setter('height'))
        self.tagBox.bind(minimum_height=self.tagBox.setter('height'))
        self.addedTagBox.bind(minimum_height=self.addedTagBox.setter('height'))
        self.tagSelects = []
        self.clearFilters()
        global SEARCH_BLACKLIST
        SEARCH_BLACKLIST = []
        self.mainScrollView.scroll_wheel_distance = CONFIG_SCROLL_SPEED
        self.updateTagSelects(TAGS)

    def searchForImages(self):
        global IMAGES, TAGGED_IMAGES
        self.loadedImage = []
        imagesRemaining = 0

        if len(self.filterTags) == 0:
            temp = [i for i in IMAGES if self.searchText in i and not i in PALLET and not i in SEARCH_BLACKLIST]
            for i in range(0, min(CONFIG_SEARCHVIEW_IMAGE_COUNT, len(temp))):
                self.loadedImage.append(temp[i])
            imagesRemaining = max(0, len(temp)-CONFIG_SEARCHVIEW_IMAGE_COUNT)

        else:
            temp = []
            if not self.tagBlackListMode:
                temp = TAGGED_IMAGES[self.filterTags[0]].copy()
                for tag in self.filterTags:
                    temp = list(set(temp).intersection(TAGGED_IMAGES[tag])) # brute force
            else: # select only the images that dont have the tags
                temp = IMAGES.copy()
                for tag in self.filterTags:
                    temp = list(set(temp).difference(TAGGED_IMAGES[tag])) # brute force
            
            temp = [i for i in temp if self.searchText in i and not i in PALLET and not i in SEARCH_BLACKLIST]
            for i in range(0, min(CONFIG_SEARCHVIEW_IMAGE_COUNT, len(temp))):
                self.loadedImage.append(temp[i])
            imagesRemaining = max(0, len(temp)-CONFIG_SEARCHVIEW_IMAGE_COUNT)

        self.loadBtn.text = "Load More [" + str(imagesRemaining) + "]"
        self.loadImages()
    
    def loadImages(self):
        self.id = uuid.uuid4()
        self.imageList1.clear_widgets()
        self.imageList2.clear_widgets()
        self.imageList3.clear_widgets()
        self.il1_height = 0
        self.il2_height = 0
        self.il3_height = 0
        for i in range(len(self.loadedImage)):
            UPDATE_QUEUE.append(partial(self.loadImage, self.loadedImage[i], self.id))
    
    def loadImage(self, img, caller_id):
        if self.id != caller_id:
            raise UpdateSkipped()

        loaded_img = SearchedImage(self)
        loaded_img.img.source = PATH + img
        img_height = 1/loaded_img.img.image_ratio
        min_height = min(self.il1_height, self.il2_height, self.il3_height)
        if min_height == self.il1_height:
            self.il1_height += img_height
            loaded_img.myColumn = 1
            self.imageList1.add_widget(loaded_img)
        elif min_height == self.il2_height:
            loaded_img.myColumn = 2
            self.il2_height += img_height
            self.imageList2.add_widget(loaded_img)
        elif min_height == self.il3_height:
            loaded_img.myColumn = 3
            self.il3_height += img_height
            self.imageList3.add_widget(loaded_img)

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
    
    def loadMoreImages(self):
        currentImageCount = len(self.loadedImage)
        imagesRemaining = 0

        if len(self.filterTags) == 0:
            temp = [i for i in IMAGES if self.searchText in i and not i in PALLET and not i in SEARCH_BLACKLIST and not i in self.loadedImage]
            for i in range(0, min(CONFIG_SEARCHVIEW_IMAGE_COUNT, len(temp))):
                self.loadedImage.append(temp[i])
            imagesRemaining = max(0, len(temp)-CONFIG_SEARCHVIEW_IMAGE_COUNT)

        else:
            temp = []
            if not self.tagBlackListMode:
                temp = TAGGED_IMAGES[self.filterTags[0]].copy()
                for tag in self.filterTags:
                    temp = list(set(temp).intersection(TAGGED_IMAGES[tag])) # brute force
            else: # select only the images that dont have the tags
                temp = IMAGES.copy()
                for tag in self.filterTags:
                    temp = list(set(temp).difference(TAGGED_IMAGES[tag])) # brute force
            
            temp = [i for i in temp if self.searchText in i and not i in PALLET and not i in SEARCH_BLACKLIST and not i in self.loadedImage]
            for i in range(0, min(CONFIG_SEARCHVIEW_IMAGE_COUNT, len(temp))):
                self.loadedImage.append(temp[i])
            imagesRemaining = max(0, len(temp)-CONFIG_SEARCHVIEW_IMAGE_COUNT)

        for i in range(currentImageCount, len(self.loadedImage)):
            UPDATE_QUEUE.append(partial(self.loadImage, self.loadedImage[i], self.id))
        
        self.loadBtn.text = "Load More [" + str(imagesRemaining) + "]"
    
    def switchTagMod_blacklist(self):
        self.tagBlackListMode = not self.tagBlackListMode
        if self.tagBlackListMode:
            self.blacklistTagsBtn.text = "Tag Blacklist [ON]"
        else:
            self.blacklistTagsBtn.text = "Tag Blacklist [OFF]"
        self.searchForImages()
        

    def clearBlacklist(self):
        global SEARCH_BLACKLIST
        SEARCH_BLACKLIST = []
        self.searchTags()
        self.searchForImages()
        self.updateBlacklist()

    def updateBlacklist(self):
        self.blacklistBtn.text = "Clear Blacklist [" + str(len(SEARCH_BLACKLIST)) + "]"

    def searchTags(self, text = None):
        if text == None:
            text = self.tagSearchText
        else:
            self.tagSearchText = text
        res = [i for i in TAGS if text in i and not i in self.filterTags] # Very inefficiant
        self.updateTagSelects(res)
    
    def updateTagSelects(self, tags):
        for tagSelect in self.tagSelects:
            self.tagBox.remove_widget(tagSelect)

        for i in range(0, min(len(tags), CONFIG_TAG_SEARCH_COUNT)):
            self.tagSelects.append(TagSelect(self))
            self.tagBox.add_widget(self.tagSelects[i])
            self.tagSelects[i].setTag(tags[i])

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
    palletIndex = 0

    def __init__(self, page, index, **kwargs):
        self.palletPage = page
        self.palletIndex = index
        super().__init__(**kwargs)

    def removeFromPallet(self):
        img = os.path.basename(self.img.source)
        if img in PALLET:
            PALLET.remove(img)
            self.palletPage.loadImages()
            os.remove("database/pallet/" + img) 

    def selectImage(self):
        self.palletPage.setMainImage(self.palletIndex)
        #self.palletPage.fullImageView.source = self.img.source
        #self.palletPage.fullImageName.text = os.path.basename(self.img.source)

class PalletPage(Widget):
    palletImageArray = []
    currentViewIndex = 0

    def build(self):
        self.imageList1.bind(minimum_height=self.imageList1.setter('height'))
        self.imageList2.bind(minimum_height=self.imageList2.setter('height'))
        self.imageList3.bind(minimum_height=self.imageList3.setter('height'))
        self.loadImages()

    def loadImages(self):
        self.palletImageArray = []
        index = 1
        self.imageList1.clear_widgets()
        self.imageList2.clear_widgets()
        self.imageList3.clear_widgets()
        il1_height = 0
        il2_height = 0
        il3_height = 0
        for img in PALLET:
            loaded_img = PalletImage(self, len(self.palletImageArray))
            self.palletImageArray.append(loaded_img)
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
    
    def nextImage(self):
        self.setMainImage(self.currentViewIndex+1)

    def prevImage(self):
        self.setMainImage(self.currentViewIndex-1)

    def setMainImage(self, index):
        self.currentViewIndex = index % len(self.palletImageArray)
        img = self.palletImageArray[self.currentViewIndex].img
        self.fullImageView.source = img.source
        self.fullImageName.text = os.path.basename(img.source)

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
        Clock.schedule_interval(update, 1.0 / CONFIG_UPDATE_SPEED)

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

def goToRoot():
    # change directory to script root
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

def update(dt):
    global UPDATE_QUEUE

    if len(UPDATE_QUEUE) == 0:
        return
    func = UPDATE_QUEUE.pop()

    try:
        func()
        pass
    except UpdateSkipped as e:
        update(0)
    except:
        print("An exception occurred") 

class UpdateSkipped(Exception):
    pass

if __name__ == "__main__":
    ImageSorterApp().run()

    