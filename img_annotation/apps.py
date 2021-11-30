from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import (
    PluginSettings,
    PluginURLs,
    ProjectType,
    SettingsType,
)


class ImgAnnotationConfig(AppConfig):
    name = 'img_annotation'
    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: "settings.common"}
                    },
            ProjectType.LMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: "settings.common"}
                    },
        },
    }
