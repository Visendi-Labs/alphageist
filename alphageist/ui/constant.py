import os

ASSETS_DIRECTORY: str = os.path.join("alphageist", "ui", "assets")


class COLOR:
    # Visendi Dark Theme
    OBSIDIAN_SHADOW = "#212124"
    GRAPHITE_DUST = "#323232"
    DOVE_GRAY = "#565658"
    WHITE = "#ffffff"
    STEEL_HAZE = "#888888"
    COSMIC_SAPPHIRE = "#556FDA"
    DREAMY_SKY = "#8FA4FC"
    SUNSET_RED = "#DB504A"
    APRICOT_BREEZE = "#FA8D88"


class DESIGN:
    ELEMENT_RADIUS = "10px"

    BUTTON_RADIUS = "10px"
    BUTTON_FONT_SIZE = "14px"
    BUTTON_HEIGHT = 35
    BUTTON_ICON_WIDTH = 35
    BUTTON_ICON_HEIGHT = BUTTON_HEIGHT

    BUTTON_CANCEL_WIDTH = 100
    BUTTON_SAVE_WIDTH = 180
    BUTTON_ADD_FOLDER_WIDTH = 70

    FONT_FAMILY = "Arial, sans-serif"
