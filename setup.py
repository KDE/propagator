from setuptools import setup, find_packages

setup(
    name             = "propagator",
    version          = "0.1.96",
    author           = "Boudhayan Gupta",
    author_email     = "bgupta@kde.org",
    description      = ("A git mirror fleet manager"),
    license          = "BSD",
    keywords         = "git mirror devops",
    url              = "http://www.kde.org/",
    packages         = find_packages(),
    install_requires = (
        "simplejson",
        "GitPython",
        "pika",
        "logbook",
        "circus"
    ),
    classifiers      = (
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Version Control",
        "Topic :: System :: Software Distribution"
    ),
    entry_points     = {
        "console_scripts": (
            "propagator-agent = propagator.agent:main",
            "propagator-remoteslave = propagator.remoteslave:main",
            "propagator-mirrorsync = propagator.utils.mirrorsync:main",
            "propagator-mirrorctl = propagator.utils.mirrorctl:main"
        ),
    },
)
