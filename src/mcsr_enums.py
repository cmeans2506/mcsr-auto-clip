from enum import Enum, StrEnum
from PyQt6.QtCore import QCoreApplication

class MatchType(Enum):
    CASUAL_MATCH = 1
    RANKED_MATCH = 2
    PRIVATE_ROOM_MATCH = 3
    EVNET_MODE_MATCH = 4

    @property
    def label(self):
        return {
            self.CASUAL_MATCH: QCoreApplication.translate("MatchType", "Casual Match"),
            self.RANKED_MATCH: QCoreApplication.translate("MatchType", "Ranked Match"),
            self.PRIVATE_ROOM_MATCH: QCoreApplication.translate("MatchType", "Private Room Match"),
            self.EVNET_MODE_MATCH: QCoreApplication.translate("MatchType", "Event Mode Match"),
        }.get(self, "")


class SeedType(StrEnum):
    BURIED_TREASURE = "BURIED_TREASURE"
    SHIPWRECK = "SHIPWRECK"
    VILLAGE = "VILLAGE"
    DESERT_TEMPLE = "DESERT_TEMPLE"
    RUINED_PORTAL = "RUINED_PORTAL"

    @property
    def label(self):
        return {
            self.BURIED_TREASURE: QCoreApplication.translate("SeedType", "Buried Treasure"),
            self.SHIPWRECK: QCoreApplication.translate("SeedType", "Shipwreck"),
            self.VILLAGE: QCoreApplication.translate("SeedType", "Village"),
            self.DESERT_TEMPLE: QCoreApplication.translate("SeedType", "Desert Temple"),
            self.RUINED_PORTAL: QCoreApplication.translate("SeedType", "Ruined Portal"),
        }.get(self, "")


class BastionType(StrEnum):
    BRIDGE = "BRIDGE"
    STABLES = "STABLES"
    HOUSING = "HOUSING"
    TREASURE = "TREASURE"

    @property
    def label(self):
        return {
            self.BRIDGE: QCoreApplication.translate("BastionType", "Bridge"),
            self.STABLES: QCoreApplication.translate("BastionType", "Stables"),
            self.HOUSING: QCoreApplication.translate("BastionType", "Housing"),
            self.TREASURE: QCoreApplication.translate("BastionType", "Treasure"),
        }.get(self, "")


class TimelineType(StrEnum):
    ENTER_THE_NETHER = "story.enter_the_nether"
    FIND_BASTION = "nether.find_bastion"
    FIND_FORTRESS = "nether.find_fortress"
    BLIND_TRAVEL = "projectelo.timeline.blind_travel"
    FOLLOW_ENDER_EYE = "story.follow_ender_eye"
    ENTER_THE_END = "story.enter_the_end"
    KILL_DRAGON = "end.kill_dragon"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        # 当收到不在定义范围内的字符串时，统一返回 UNKNOWN
        return cls.UNKNOWN

    @property
    def label(self):
        return {
            self.ENTER_THE_NETHER: QCoreApplication.translate("TimelineType", "Nether"),
            self.FIND_BASTION: QCoreApplication.translate("TimelineType", "Bastion"),
            self.FIND_FORTRESS: QCoreApplication.translate("TimelineType", "Fortress"),
            self.BLIND_TRAVEL: QCoreApplication.translate("TimelineType", "Blind"),
            self.FOLLOW_ENDER_EYE: QCoreApplication.translate("TimelineType", "Stronghold"),
            self.ENTER_THE_END: QCoreApplication.translate("TimelineType", "End"),
            self.KILL_DRAGON: QCoreApplication.translate("TimelineType", "Dragon Kill"),
        }.get(self, "")


class EventIdType(StrEnum):
    ENTER_NETHER = "rsg.enter_nether"
    ENTER_BASTION = "rsg.enter_bastion"
    ENTER_FORTRESS = "rsg.enter_fortress"
    FIRST_PORTAL = "rsg.first_portal"
    SECOND_PORTAL = "rsg.second_portal"
    ENTER_STRONGHOLD = "rsg.enter_stronghold"
    ENTER_END = "rsg.enter_end"
    FINISH = "rsg.credits"

    @property
    def label(self):
        return {
            self.ENTER_NETHER: QCoreApplication.translate("EventIdType", "Enter Nether"),
            self.ENTER_BASTION: QCoreApplication.translate("EventIdType", "Enter Bastion"),
            self.ENTER_FORTRESS: QCoreApplication.translate("EventIdType", "Enter Fortress"),
            self.FIRST_PORTAL: QCoreApplication.translate("EventIdType", "First Portal"),
            self.SECOND_PORTAL: QCoreApplication.translate("EventIdType", "Second Portal"),
            self.ENTER_STRONGHOLD: QCoreApplication.translate("EventIdType", "Enter Stronghold"),
            self.ENTER_END: QCoreApplication.translate("EventIdType", "Enter End"),
            self.FINISH: QCoreApplication.translate("EventIdType", "Finish"),
        }.get(self, "")

    @property
    def abbr(self):
        return {
            self.ENTER_NETHER: QCoreApplication.translate("EventIdType", "NE"),
            self.ENTER_BASTION: QCoreApplication.translate("EventIdType", "Bas"),
            self.ENTER_FORTRESS: QCoreApplication.translate("EventIdType", "Fort"),
            self.FIRST_PORTAL: QCoreApplication.translate("EventIdType", "Blind"),
            self.SECOND_PORTAL: QCoreApplication.translate("EventIdType", "Second Portal"),
            self.ENTER_STRONGHOLD: QCoreApplication.translate("EventIdType", "SH"),
            self.ENTER_END: QCoreApplication.translate("EventIdType", "EE"),
            self.FINISH: QCoreApplication.translate("EventIdType", "Finish"),
        }.get(self, "")

