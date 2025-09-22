from setuptools import setup, find_packages

setup(
    name="img_annotation",
    version="1.0.1",
    author="Oficina EOL UChile",
    author_email="eol-ing@uchile.cl",
    description="Xblock with a viewer for high-resolution zoomable images. It lets both students and instructors add annotations over it.",
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
