# SPDX-FileCopyrightText: none
#
# SPDX-License-Identifier: CC0-1.0
let
  hostPkgs = import <nixpkgs> {};
  pkgs = import (hostPkgs.fetchFromGitHub {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "5b4ee341ea0a5f2cad8ccd5725d0a63ed97ded38";
    sha256 = "sha256-Ykt1BL5xPF4K6uh6j5KhZjUCCp+GE2d6QGKXApsWRlA=";
  }) {};
in hostPkgs.mkShell {
  buildInputs = [
    pkgs.cypress
    pkgs.nodejs-16_x
    pkgs.python3
    pkgs.python3.pkgs.requests
    pkgs.python3.pkgs.numpy
    pkgs.python3.pkgs.pandas
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
