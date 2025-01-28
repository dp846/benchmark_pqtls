#!/bin/bash
set -ex

# NOTE: the following is assumed:
# - script assumes the following `apt` dependencies are already installed: git build-essential perl cmake autoconf libtool zlib1g-dev
# - These are not installed in this script to avoid any dangerous use of `sudo`:
# - The script should be run from the repository root (and hence the environment variable ROOT_DIR is set to the local path to the repository root)

### --- Env variables and setup --- ###

# Paths
ROOT_DIR=$(pwd)
THIRD_PARTY_DIR="$ROOT_DIR/third_party" # installation location for all third party dependency source code (all built from source)
FINAL_BUILD_DIR="$ROOT_DIR/provider_build" # location of final build artifacts for liboqs, openssl, and the provider libraries
LIBOQS_DIR="$THIRD_PARTY_DIR/liboqs" # oqs source dir 
OPENSSL_DIR="$THIRD_PARTY_DIR/openssl" # openssl source dir
OQSPROVIDER_DIR="$THIRD_PARTY_DIR/oqs-provider" # provider source dir

# Commit hashes (used to keep granular consistency in versions used of OQS, OpenSSL, and the provider)
OPENSSL_COMMIT_HASH=cf28777
LIBOQS_COMMIT_HASH=f877812
OQSPROVIDER_COMMIT_HASH=afc1de2

# Make directories for source and build artifacts
mkdir -p $THIRD_PARTY_DIR
mkdir -p $FINAL_BUILD_DIR/lib64
if [ ! -L "$FINAL_BUILD_DIR/lib" ]; then
    ln -s $FINAL_BUILD_DIR/lib64 $FINAL_BUILD_DIR/lib
fi

### --- Installing OpenSSL --- ###

if [ ! -d "$OPENSSL_DIR" ]; then

  # Clone
  cd $THIRD_PARTY_DIR
  git clone https://github.com/openssl/openssl.git
  cd openssl
  git checkout $OPENSSL_COMMIT_HASH
  
  # Build and install
  ./Configure \
    --prefix=$FINAL_BUILD_DIR \
    no-ssl no-tls1 no-tls1_1 no-afalgeng \
    no-shared threads -lm
  make -j $(nproc)
  make -j $(nproc) install_sw install_ssldirs
else
  echo "openssl directory already exists in third_party. Skipping installation..."
fi

### --- Installing liboqs --- ###

if [ ! -d "$LIBOQS_DIR" ]; then

  # Clone
  cd $THIRD_PARTY_DIR
  git clone https://github.com/open-quantum-safe/liboqs.git
  cd liboqs
  git checkout $LIBOQS_COMMIT_HASH
  
  # Build and install
  mkdir build && cd build
  cmake \
    -DCMAKE_INSTALL_PREFIX=$FINAL_BUILD_DIR \
    -DBUILD_SHARED_LIBS=ON \
    -DOQS_USE_OPENSSL=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DOQS_BUILD_ONLY_LIB=ON \
    -DOQS_DIST_BUILD=ON \
    ..
  make -j $(nproc)
  make -j $(nproc) install
else
  echo "liboqs directory already exists in third_party. Skipping installation..."
fi

### --- Installing OQS OpenSSL Provider --- ###

if [ ! -d "$OQSPROVIDER_DIR" ]; then

  # Clone
  cd $THIRD_PARTY_DIR
  git clone https://github.com/open-quantum-safe/oqs-provider.git
  cd oqs-provider
  git checkout $OQSPROVIDER_COMMIT_HASH
  
  # Build and install
  liboqs_DIR=$FINAL_BUILD_DIR cmake \
    -DCMAKE_INSTALL_PREFIX=$THIRD_PARTY_DIR/oqs-provider \
    -DOPENSSL_ROOT_DIR=$FINAL_BUILD_DIR \
    -DCMAKE_BUILD_TYPE=Release \
    -S . \
    -B _build
  cmake --build _build

  # Manually copy build files over
  cp _build/lib/* $FINAL_BUILD_DIR/lib/

  # Edit openssl config to use the oqsprovider
  sed -i "s/default = default_sect/default = default_sect\noqsprovider = oqsprovider_sect/g" $FINAL_BUILD_DIR/ssl/openssl.cnf &&
  sed -i "s/\[default_sect\]/\[default_sect\]\nactivate = 1\n\[oqsprovider_sect\]\nactivate = 1\n/g" $FINAL_BUILD_DIR/ssl/openssl.cnf

  # Set required env vars
  export OPENSSL_CONF=$FINAL_BUILD_DIR/ssl/openssl.cnf
  export OPENSSL_MODULES=$FINAL_BUILD_DIR/lib
  $FINAL_BUILD_DIR/bin/openssl list -providers -verbose -provider oqsprovider  
else
  echo "oqs-provider directory already exists in third_party. Skipping installation..."
fi

### --- Installing NGINX --- ###
NGINX_VERSION=1.25.3
NGINX_DIR="$THIRD_PARTY_DIR/nginx-$NGINX_VERSION"

if [ ! -d "$NGINX_DIR" ]; then
    cd $THIRD_PARTY_DIR
    wget http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz
    tar xzf nginx-$NGINX_VERSION.tar.gz
    rm nginx-$NGINX_VERSION.tar.gz
fi

cd $NGINX_DIR

# Configure NGINX to use custom OpenSSL
./configure \
    --prefix=$FINAL_BUILD_DIR/nginx \
    --with-http_ssl_module \
    --with-cc-opt="-I$FINAL_BUILD_DIR/include" \
    --with-ld-opt="-L$FINAL_BUILD_DIR/lib -Wl,-rpath,$FINAL_BUILD_DIR/lib"

make -j $(nproc)
make install

# Verify NGINX uses the correct OpenSSL
$FINAL_BUILD_DIR/nginx/sbin/nginx -V
