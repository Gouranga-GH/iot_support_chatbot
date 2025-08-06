from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="IoT Support Chatbot",
    version="0.1",
    author="Gouranga",
    packages=find_packages(),
    install_requires=requirements,
) 