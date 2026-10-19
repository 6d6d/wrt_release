#!/usr/bin/env python3
"""Check the resolved M2 configuration and the actual firmware package lists."""

import argparse
import re
from pathlib import Path

USB_PACKAGES = {
    "kmod-usb3", "kmod-usb-xhci-hcd", "kmod-usb-dwc3",
    "kmod-usb-dwc3-qcom", "kmod-usb-storage", "kmod-usb-storage-uas",
}
FORBIDDEN = re.compile(
    r"(?:mosdns|luci-app-mosdns|luci-app-passwall.*|"
    r"kmod-ath.*|kmod-cfg80211|kmod-mac80211.*|ath11k-firmware.*|"
    r"ipq-wifi-.*|wpad.*|hostapd.*|wpa-supplicant.*|"
    r"kmod-qca-nss-drv-wifi-.*)"
)


def verify(packages, label, built_as_modules=None):
    problems = []
    missing = USB_PACKAGES - packages
    unwanted = {name for name in packages if FORBIDDEN.fullmatch(name)}
    if built_as_modules:
        unwanted.update(name for name in built_as_modules if FORBIDDEN.fullmatch(name))
    if missing:
        problems.append("missing USB packages: " + ", ".join(sorted(missing)))
    if unwanted:
        problems.append("unwanted packages: " + ", ".join(sorted(unwanted)))
    if problems:
        raise SystemExit(f"{label}: " + "; ".join(problems))
    print(f"{label}: USB 3.0/UAS present; MosDNS, Passwall and Wi-Fi packages absent")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--target-dir", type=Path)
    args = parser.parse_args()
    if not (args.config or args.target_dir):
        parser.error("provide --config or --target-dir")
    if args.config:
        text = args.config.read_text()
        installed = set(re.findall(r"^CONFIG_PACKAGE_([^=]+)=y$", text, re.M))
        modules = set(re.findall(r"^CONFIG_PACKAGE_([^=]+)=m$", text, re.M))
        verify(installed, str(args.config), modules)
    if args.target_dir:
        manifests = sorted(
            p for p in args.target_dir.rglob("*.manifest") if p.name != "Packages.manifest"
        )
        if not manifests:
            raise SystemExit(f"No firmware manifests found in {args.target_dir}")
        for manifest in manifests:
            packages = {line.split()[0] for line in manifest.read_text().splitlines() if line.strip()}
            verify(packages, str(manifest))


if __name__ == "__main__":
    main()
