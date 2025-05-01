FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装基本依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
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

# 安装 buildozer
RUN pip3 install --upgrade pip && \
    pip3 install buildozer Cython==0.29.33

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 初始化 buildozer
RUN buildozer android update

# 构建 APK
CMD ["buildozer", "android", "debug"] 