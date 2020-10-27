from setuptools import setup

setup(
    name="visual_novel_4k",
    version="0.1.0",
    packages=["visual_novel_4k"],
    entry_points={
        "console_scripts": [
            "visual_novel_4k = visual_novel_4k.__main__:main"
        ]
    },
)