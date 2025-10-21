# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This software may be used and distributed in accordance with
# the terms of the DINOv3 License Agreement.

# ------------------------------------------------------------------------------------------------
# Deformable DETR
# Copyright (c) 2020 SenseTime. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------------------------------
# Modified from https://github.com/chengdazhi/Deformable-Convolution-V2-PyTorch/tree/pytorch_1.0.0
# ------------------------------------------------------------------------------------------------

import os
import shutil
import glob

from setuptools import find_packages, setup

from torch.utils.cpp_extension import (
    CppExtension,
    CUDAExtension,
    BuildExtension,
    CUDA_HOME,
)

def get_extensions():
    debug_mode = os.getenv("DEBUG", "0") == "1"
    if debug_mode:
        print("Compiling in debug mode")

    # Build CUDA if CUDA toolkit is present, even if no GPUs are visible
    has_nvcc = shutil.which("nvcc") is not None
    has_cuda_toolkit = (CUDA_HOME is not None) or has_nvcc
    use_cuda = has_cuda_toolkit
    extension = CUDAExtension if use_cuda else CppExtension

    extra_link_args = ["-fopenmp"]
    extra_compile_args = {
        "cxx": [
            "-O3" if not debug_mode else "-O0",
            "-fdiagnostics-color=always",
            "-fopenmp",
        ],
    }
    if use_cuda:
        # Preserve FP16-related flags
        extra_compile_args["nvcc"] = [
            "-O3" if not debug_mode else "-O0",
            "-DCUDA_HAS_FP16=1",
            "-D__CUDA_NO_HALF_OPERATORS__",
            "-D__CUDA_NO_HALF_CONVERSIONS__",
            "-D__CUDA_NO_HALF2_OPERATORS__",
        ]

    if debug_mode:
        extra_compile_args["cxx"].append("-g")
        if use_cuda:
            extra_compile_args["nvcc"].append("-g")
        extra_link_args.extend(["-O0", "-g"])

    this_dir = os.path.dirname(os.path.abspath(__file__))
    extensions_dir = os.path.join(this_dir, "src")

    main_file = glob.glob(os.path.join(extensions_dir, "*.cpp"))
    source_cpu = glob.glob(os.path.join(extensions_dir, "cpu", "*.cpp"))
    source_cuda = glob.glob(os.path.join(extensions_dir, "cuda", "*.cu"))

    sources = main_file + source_cpu
    define_macros = []
    if use_cuda:
        sources += source_cuda
        define_macros += [("WITH_CUDA", None)]

    # Convert sources to relative paths for setuptools (absolute sources not allowed)
    sources = [os.path.relpath(p, this_dir) for p in sources]
    # Use absolute include dir so ninja build (run from temp dir) still finds headers
    include_dirs = [extensions_dir]
    ext_modules = [
        extension(
            "MultiScaleDeformableAttention",
            sources,
            include_dirs=include_dirs,
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
        )
    ]
    return ext_modules


setup(
    packages=find_packages(
        exclude=(
            "configs",
            "tests",
        )
    ),
    ext_modules=get_extensions(),
    cmdclass={"build_ext": BuildExtension},
)
