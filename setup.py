
import os

from setuptools import setup

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
    version="0.0.1",
    author="Luis Santana",
    author_email="luis.santana@uchile.cl",
    description=".",
    url="https://eol.uchile.cl",
    packages=["img_annotation"],
    install_requires=[
        'XBlock',
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
    package_data=package_data("img_annotation", ["static", "public"]),
)
