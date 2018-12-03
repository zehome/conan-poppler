#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import shutil


class LibpopplerConan(ConanFile):
    name = "poppler"
    version = "0.71.0"
    description = "Poppler is a PDF rendering library based on the xpdf-3.0 code base"
    topics = ("conan", "libpoppler", "poppler", "pdf")
    url = "https://github.com/zehome/conan-poppler"
    homepage = "https://poppler.freedesktop.org/"
    author = "Laurent Coustet <ed@zehome.com>"
    license = "GPL-3.0-only"
    generators = "cmake"
    exports_sources = "CMakeLists.txt", "patches/*.diff"
    settings = "os", "compiler", "build_type", "arch"

    _source_subfolder = "poppler-src"
    
    options = {
        "shared": [True, False], "with_lcms": [True, False],
        "with_cpp": [True, False], "with_cairo": [True, False],
        "with_qt": [True, False], "with_splash": [True, False],
        "with_curl": [True, False],
    }
    default_options = (
        "shared=False", "with_qt=False", "with_lcms=False", "with_cpp=False",
        "with_cairo=False", "with_curl=False",
        #LC: Specific
        "libpng:shared=False",
        "freetype:with_png=False", "freetype:shared=False", "freetype:with_zlib=False",
        "zlib:shared=False",
        "openjpeg:shared=False",
        "cairo:shared=False",
        "glib:shared=False",
        "libcurl:shared=False", "OpenSSL:shared=False",
        "Qt:opengl=desktop", "Qt:qtxmlpatterns=True", "Qt:shared=True",
    )

    requires = (
        "zlib/1.2.11@conan/stable",
        "libpng/1.6.34@bincrafters/stable",
        "libjpeg/9c@bincrafters/stable",
        "openjpeg/2.3.0@bincrafters/stable",
        "libtiff/4.0.9@bincrafters/stable",
        "freetype/2.9.0@bincrafters/stable",
    )

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("cairo")

    def configure(self):
        if self.options.with_lcms:
            self.requires.add("lcms/2.9@bincrafters/stable")
        if self.options.with_qt:
            self.requires.add("Qt/5.11.2@bincrafters/testing")
        if self.settings.os != "Windows" and self.options.with_cairo:
            self.requires.add("cairo/1.15.14@bincrafters/stable")
            self.requires.add("glib/2.56.1@bincrafters/stable")
        if self.settings.os == "Windows" and not self.options.with_splash:
            raise ConanInvalidConfiguration("Option with_splash=True is mandatory on windows")
        if self.options.with_curl:  # TODO: does not link on windows / shared=False
            self.requires.add("libcurl/7.61.1@bincrafters/stable")

    def source(self):
        source_url = "https://poppler.freedesktop.org/"
        tools.get("{0}/poppler-{1}.tar.xz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version

        if os.path.exists(self._source_subfolder):
            shutil.rmtree(self._source_subfolder)
        os.rename(extracted_dir, self._source_subfolder)
        # TODO: Ugly.. May need to be replaced by something
        # better
        os.rename(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                  os.path.join(self._source_subfolder, "CMakeListsOriginal.txt"))
        shutil.copy("CMakeLists.txt",
                    os.path.join(self._source_subfolder, "CMakeLists.txt"))
        # if self.settings.os == "Windows":
        #     tools.patch(
        #         self._source_subfolder,
        #         patch_file=os.path.join("patches", "poppler-export.diff"), strip=1)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.verbose = True
        cmake.definitions["ENABLE_SPLASH"] = self.options.with_splash
        cmake.definitions["ENABLE_ZLIB"] = True
        cmake.definitions["BUILD_QT5_TESTS"] = False
        cmake.definitions["ENABLE_CPP"] = self.options.with_cpp
        cmake.definitions["ENABLE_CMS"] = "lcms2" if self.options.with_lcms else 'none'
        cmake.definitions["ENABLE_LIBCURL"] = self.options.with_curl
        if self.settings.os == "Windows":
            cmake.definitions["LIB_SUFFIX"] = ""
            cmake.definitions["FONT_CONFIGURATION"] = "win32"
        cmake.definitions["BUILD_SHARED_LIBS"] = self.options.shared
        cmake.configure(source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        #shutil.rmtree(os.path.join(self._source_subfolder, 'cmake'))
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)