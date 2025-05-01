FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装必要的包
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    wget \
    unzip \
    default-jdk \
    libssl-dev \
    libffi-dev \
    libltdl-dev \
    zip \
    && rm -rf /var/lib/apt/lists/*

# 安装buildozer
RUN pip3 install --upgrade pip
RUN pip3 install buildozer Cython==0.29.33

# 安装Android SDK和NDK依赖
RUN buildozer android update

WORKDIR /app

COPY . /app/

# 构建命令
CMD ["buildozer", "android", "debug"] 