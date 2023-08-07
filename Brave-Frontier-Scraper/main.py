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
SAVE_PATH = Path("./db/bf1_units/")
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

        self._soup = BeautifulSoup(page, "html.parser")

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
        '''Returns all public attributes in a json-readable format.'''
        return {k:val for k,val in self.__dict__.items() if not k.startswith("_")}

    def get_unit_id(self) -> str:
        '''Grabs the unit's id.'''
        if not self.uid:
            id_tag = self._soup.select_one('div[class="unit_detail_number"] > span[class="number"]')
            if id_tag:
                self.uid = id_tag.text.strip().lstrip("No.")
        
        return self.uid

    def get_unit_name(self) -> str:
        '''Grabs the unit's name.'''
        if not self.name:
            name_tag = self._soup.select_one('div[class="unit_detail_name"] > p[class="name"]')
            self.name = name_tag.text.strip()

        return self.name

    def get_unit_series(self) -> str:
        '''Grabs what series the unit belonged to.'''
        if not self.series:
            series_tag = self._soup.select_one('div[class="unit_detail_number"] > span[class="series"]')
            if series_tag:  # There are some units that do not belong to a series.
                self.series = series_tag.text.strip().lstrip("≪").rstrip("≫")
        
        return self.series

    def get_unit_attribute(self) -> str:
        '''Grabs the unit's attribute.'''
        if not self.attribute:
            attr_tag = self._soup.select_one('div[class="unit_detail_name"] > div[class="zokusei"] > img[src]')
            attribute = attr_tag.get("src")[-5]
            # if attribute in UnitElements
            if UnitElements.has_value(int(attribute)):
                self.attribute = UnitElements(int(attribute)).name

        return self.attribute
    
    def get_unit_rank(self) -> int:
        '''Grabs the unit's rank.'''
        if not self.rank:
            rank_tag = self._soup.select_one('div[class="rank"] > img[src]')
            if rank_tag:
                self.rank = rank_tag.get("src")[-5]

        return self.rank
    
    def get_unit_sex(self) -> str:
        '''Grabs the unit's sex.'''
        if not self.sex:
            sex_tag = self._soup.select_one('div[class="sex"] > img[src]')
            if sex_tag:
                self.sex = sex_tag.get("src").split("_")[-1].replace(".png", "")

        return self.sex
    
    
    def get_unit_animations(self) -> List[str]:
        '''Grabs a list of urls containing the unit animations
        (default, idle, and attack).'''
        if (len(self.animations) == 3) or (len(self.animations) != 0):
            return self.animations
        else:
            animation_tags = self._soup.select('div[class="unit_gif"] > img[src]')
            self.animations = [urljoin(self.base_url, animation.get("src")) for animation in animation_tags]
            return self.animations

    def get_unit_text(self) -> str:
        '''Grabs the unit's description.'''
        if self.unit_text:
            return self.unit_text
        else:
            text_tag = self._soup.select_one('article[class="unit_text"]')
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

    _soup = BeautifulSoup(resp, "html.parser")

    # Get all tags for each Brave Frontier unit
    for unit_tag in _soup.select('ul[class="unit_list"] > li'):

        uid = unit_tag.select_one('span').text.lstrip("No.")

        # Create a path to store unit data
        unit_folder = SAVE_PATH / uid
        unit_folder.mkdir(exist_ok=True)

        # Skip existing entries
        if (unit_folder / "data.json").exists():
            LOG.warning(f"{uid} already exists. Brave Frontier unit skipped.")
            continue

        # Get url to the unit's profile
        link_tag = unit_tag.select_one('a[href^="bf"]')
        link_to_profile = urljoin(BASE_URL, link_tag.get("href"))

        LOG.info(f"Downloading unit {uid} profile")
        unit = UnitPage(link_to_profile)

        # Add unit icon to unit info
        unit_icon_tag = link_tag.select_one('img[src]')
        if unit_icon_tag:
            unit_icon = unit_icon_tag.get("src")
            unit.icon = unit_icon

        # Dump unit profile into folder
        with (unit_folder / "data.json").open("w+", encoding="utf-8") as outfile:
            outfile.write(json.dumps(unit.to_json(), indent=4, ensure_ascii=False))

        # Location for unit animations and images
        unit_asset_folder = unit_folder / "assets"
        unit_asset_folder.mkdir(exist_ok=True)

        # Download the unit's animations and profile icon
        LOG.info(f"Downloading unit {uid} assets.")
        url_list = [url for url in [unit.icon]+unit.animations if url is not None]
        for url in url_list:
            img_req = requests.get(url)
            asset_filename = Path(url).name

            LOG.debug(f"Downloading <{asset_filename}> to: <{unit_asset_folder}>")

            with (unit_asset_folder / asset_filename).open("wb+") as outfile:
                outfile.write(img_req.content)

        LOG.info(f"Successfully donwloaded unit {unit.uid} information.")
        # print(json.dumps(unit.to_json(), indent=4, ensure_ascii=False))

    pass


if __name__ == '__main__':
    main()