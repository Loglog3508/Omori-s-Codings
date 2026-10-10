# -*- coding: utf-8 -*-
"""大数据可视化实验 共享数据加载与绘图工具"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\omori\Omori-s-Codings\课程\大数据可视化"
DATA = os.path.join(BASE, "UN_MigFlow_All_CountryFiles")
YEARS = list(range(1980, 2014))

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110

DECADES = [
    ("1980s", 1980, 1989),
    ("1990s", 1990, 1999),
    ("2000s", 2000, 2009),
    ("2010-2013", 2010, 2013),
]


def read_sheet(file, sheet, header=20):
    df = pd.read_excel(os.path.join(DATA, file), sheet_name=sheet, header=header)
    years = [y for y in YEARS if y in df.columns]
    df = df.copy()
    for y in years:
        df[y] = pd.to_numeric(df[y], errors="coerce").fillna(0)
    return df, years


def load_canada():
    df, years = read_sheet("Canada.xlsx", "Canada by Citizenship")
    imm = df[(df["Type"] == "Immigrants") & (df["Coverage"] == "Foreigners")].copy()
    imm = imm[~imm["OdName"].isin(["Total", "Unknown"])]
    return imm, years


def load_australia():
    df, years = read_sheet("Australia.xlsx", "Australia by Residence")
    imm = df[df["Type"] == "Immigrants"].copy()
    imm = imm[~imm["OdName"].isin(["Total", "Unknown"])]
    return imm, years


def decade_series(years):
    out = {}
    for name, start, end in DECADES:
        cols = [y for y in years if start <= y <= end]
        out[name] = cols
    return out


def total(df, cols):
    return df[cols].sum(axis=1)