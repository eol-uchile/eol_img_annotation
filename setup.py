
import os

from setuptools import setup, find_packages

def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}

setup(
    name="img_annotation",
    version="1.0.0",
    author="Oficina EOL UChile",
    author_email="eol-ing@uchile.cl",
    description="Xblock with a viewer for high-resolution zoomable images. It lets both students and instructor to add annotations over it.",
    url="https://eol.uchile.cl",
    packages=find_packages(),
    install_requires=[
        'XBlock',
        'xmltodict'
        ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'xblock.v1': ['img_annotation = img_annotation:ImgAnnotationXBlock'],
        "lms.djangoapp": [
            "img_annotation = img_annotation.apps:ImgAnnotationConfig",
        ],
        "cms.djangoapp": [
            "img_annotation = img_annotation.apps:ImgAnnotationConfig",
        ],
    },
)
