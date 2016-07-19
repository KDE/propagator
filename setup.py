from setuptools import setup, find_packages

setup(
    name             = "propagator",
    version          = "1.0.0",
    author           = "Boudhayan Gupta",
    author_email     = "bgupta@kde.org",
    description      = ("A git mirror fleet manager"),
    license          = "BSD",
    keywords         = "git mirror devops",
    url              = "http://www.kde.org/",
    packages         = find_packages(),
    install_requires = (
        "GitPython",
    ),
    classifiers      = (
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
    ),
    entry_points     = {
        "console_scripts": (
            "propagator-agent = propagator.agent:main",
        ),
    },
)
