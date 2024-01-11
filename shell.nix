# SPDX-FileCopyrightText: none
#
# SPDX-License-Identifier: CC0-1.0
let
  hostPkgs = import <nixpkgs> { };
  pkgs = import
    (hostPkgs.fetchFromGitHub {
      owner = "NixOS";
      repo = "nixpkgs";
      rev = "057f9aecfb71c4437d2b27d3323df7f93c010b7e";
      sha256 = "sha256-MxCVrXY6v4QmfTwIysjjaX0XUhqBbxTWWB4HXtDYsdk=";
    })
    { };
in
hostPkgs.mkShell {
  buildInputs = [
    pkgs.cypress
    pkgs.nodejs-18_x
    (pkgs.python3.withPackages (ps: with ps; [
      autopep8
      beautifulsoup4
      fpdf
      html5lib
      lxml
      numpy
      openpyxl
      pandas
      pip
      requests
      sqlite-utils
      tabula-py
    ]))
  ];
  shellHook = ''
    export CYPRESS_INSTALL_BINARY=0
    export CYPRESS_RUN_BINARY=${pkgs.cypress}/bin/Cypress

    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
