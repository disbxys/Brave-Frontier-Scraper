import codecs
import enum
import json
from pathlib import Path
import time
from typing import Any, Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

from logger import get_logger


LOG = get_logger(__name__)

BASE_URL = "https://www.bravefrontier.jp/library/bf1/bf1_list.php"
SAVE_PATH = Path("./db/bf_units/")
if not SAVE_PATH.exists(): SAVE_PATH.mkdir(parents=True, exist_ok=True)

class UnitElements(enum.Enum):
    Fire = 1
    Water = 2
    Earth = 3
    Thunder = 4
    Light = 5
    Dark = 6

    @classmethod
    def has_value(self, value) -> bool:
        return any(elem.value == value for elem in UnitElements)


class UnitPage:
    def __init__(self, url:str):
        self.base_url = url

        req = requests.get(self.base_url)
        page = req.content

        self.soup = BeautifulSoup(page, "html.parser")

        self.uid = None
        self.icon = None
        self.name = None
        self.series = None
        self.attribute = None
        self.rank = None
        self.sex = None
        self.animations = []
        self.unit_text = None

        self.gather_data()

    def to_json(self) -> Dict[str, Any]:
        '''Returns all attributes in a json-readable format.'''
        return {k:val for k,val in self.__dict__.items() if k != "soup"}

    def get_unit_id(self) -> str:
        '''Grabs the unit's id.'''
        if not self.uid:
            id_tag = self.soup.select_one('div[class="unit_detail_number"] > span[class="number"]')
            if id_tag:
                self.uid = id_tag.text.strip().lstrip("No.")
        
        return self.uid

    def get_unit_name(self) -> str:
        '''Grabs the unit's name.'''
        if not self.name:
            name_tag = self.soup.select_one('div[class="unit_detail_name"] > p[class="name"]')
            self.name = name_tag.text.strip()

    def get_unit_series(self) -> str:
        '''Grabs what series the unit belonged to.'''
        if not self.series:
            series_tag = self.soup.select_one('div[class="unit_detail_number"] > span[class="series"]')
            self.series = series_tag.text.strip().lstrip("≪").rstrip("≫")
        
        return self.series

    def get_unit_attribute(self) -> str:
        '''Grabs the unit's attribute.'''
        if not self.attribute:
            attr_tag = self.soup.select_one('div[class="unit_detail_name"] > div[class="zokusei"] > img[src]')
            attribute = attr_tag.get("src")[-5]
            # if attribute in UnitElements
            if UnitElements.has_value(int(attribute)):
                self.attribute = UnitElements(int(attribute)).name

        return self.attribute
    
    def get_unit_rank(self) -> int:
        '''Grabs the unit's rank.'''
        if not self.rank:
            rank_tag = self.soup.select_one('div[class="rank"] > img[src]')
            if rank_tag:
                self.rank = rank_tag.get("src")[-5]

        return self.rank
    
    def get_unit_sex(self) -> str:
        '''Grabs the unit's sex.'''
        if not self.sex:
            sex_tag = self.soup.select_one('div[class="sex"] > img[src]')
            if sex_tag:
                self.sex = sex_tag.get("src").split("_")[-1].replace(".png", "")

        return self.sex
    
    
    def get_unit_animations(self) -> List[str]:
        '''Grabs a list of urls containing the unit animations
        (default, idle, and attack).'''
        if (len(self.animations) == 3) or (len(self.animations) != 0):
            return self.animations
        else:
            animation_tags = self.soup.select('div[class="unit_gif"] > img[src]')
            self.animations = [urljoin(self.base_url, animation.get("src")) for animation in animation_tags]
            return self.animations

    def get_unit_text(self) -> str:
        if self.unit_text:
            return self.unit_text
        else:
            text_tag = self.soup.select_one('article[class="unit_text"]')
            if text_tag:
                self.unit_text = text_tag.text
                return text_tag.text
            else:
                return self.unit_text

    def gather_data(self) -> None:
        '''Finds all data for each respective attribute.'''
        self.get_unit_id()
        self.get_unit_name()
        self.get_unit_series()
        self.get_unit_attribute()
        self.get_unit_rank()
        self.get_unit_sex()
        self.get_unit_animations()
        self.get_unit_text()



def main() -> None:

    req = requests.get(BASE_URL)
    time.sleep(0.5)
    resp = req.content

    soup = BeautifulSoup(resp, "html.parser")

    for unit_tag in soup.select('ul[class="unit_list"] > li'):

        uid = unit_tag.select_one('span').text.lstrip("No.")

        link_tag = unit_tag.select_one('a[href^="bf"]')
        details_link = urljoin(BASE_URL, link_tag.get("href"))
        # print(uid, details_link)

        unit = UnitPage(details_link)

        unit_icon_tag = link_tag.select_one('img[src]')
        if unit_icon_tag:
            unit_icon = unit_icon_tag.get("src")
            unit.icon = unit_icon

        print(unit.uid, unit.name)

        with (SAVE_PATH / f"{uid}.json").open("w+", encoding="utf-8") as outfile:
            outfile.write(json.dumps(unit.to_json(), indent=4, ensure_ascii=False))
        # print(json.dumps(unit.to_json(), indent=4, ensure_ascii=False))

    pass


if __name__ == '__main__':
    main()