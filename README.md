# shitty_rpm_builder #

shitty_rpm_builder is used to create a rpm of source code tarbals.

Downloads tarbals from source url and checks it's sha512 checksum. It then unpacks the tarball. it will then run `./configure` `make` `make install` into a build directory. it will then use FPM to create an RPM of the build directory for you. 

### This Repo is for creating a rpm from source code tarballs   ###

* Create RPM of source code 
* [Learn Markdown](https://guides.github.com/features/mastering-markdown/)

### Requirements
* [fpm](https://github.com/jordansissel/fpm)
* [pytoml](https://github.com/avakar/pytoml)
* Python 2.7+
* rpmbuild

### How do I get set up? ###

* Checkout this repo to your laptop of bastion host
* Populate the `util/config.toml` file with the settings you'll need to comile a package
* Make sure all requirements are installed, via `yum, dnf,`& `pip` follow instructions for `fpm` & `pytoml` on their README's

```
#!bash

../shitty_rpm_builder/
├── README.md
├── RPMS
├── shitty_rpm_builder.py
└── util
    ├── color_stream.py
    ├── config.toml
    └── __init__.py

```
* Deployment: once the RPM is created, copy it to your repository and run `createrepo --update`

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
