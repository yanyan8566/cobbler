import pathlib
import subprocess

import pytest

import cobbler.actions.mkloaders
from cobbler.actions import mkloaders
from cobbler.api import CobblerAPI


@pytest.fixture()
def api():
    return CobblerAPI()


def test_grubimage_object(api):
    # Arrange & Act
    test_image_creator = mkloaders.MkLoaders(api)

    # Assert
    assert isinstance(test_image_creator, mkloaders.MkLoaders)
    assert str(test_image_creator.syslinux_dir) == "/usr/share/syslinux"


def test_grubimage_run(api, mocker):
    # Arrange
    test_image_creator = mkloaders.MkLoaders(api)
    mocker.patch("cobbler.actions.mkloaders.symlink", spec=cobbler.actions.mkloaders.symlink)
    mocker.patch("cobbler.actions.mkloaders.mkimage", spec=cobbler.actions.mkloaders.mkimage)

    # Act
    test_image_creator.run()

    # Assert
    # On a full install: 3 common formats, 4 syslinux links and 9 bootloader formats
    # In our test container we have: shim (1x), ipxe (1x), syslinux v4 (3x) and 4 grubs (5x)
    assert mkloaders.symlink.call_count == 10
    # In our test container we have: x86_64, arm64-efi, i386-efi & i386-pc-pxe
    assert mkloaders.mkimage.call_count == 4


def test_mkimage(mocker):
    # Arrange
    mkimage_args = {
        "image_format": "grubx64.efi",
        "image_filename": pathlib.Path("/var/cobbler/loaders/grub/grubx64.efi"),
        "modules": ["btrfs", "ext2", "luks", "serial"],
    }
    mocker.patch("cobbler.actions.mkloaders.subprocess.run", spec=subprocess.run)

    # Act
    mkloaders.mkimage(**mkimage_args)

    # Assert
    mkloaders.subprocess.run.assert_called_once_with(
        [
            "grub2-mkimage",
            "--format",
            mkimage_args["image_format"],
            "--output",
            str(mkimage_args["image_filename"]),
            "--prefix=",
            *mkimage_args["modules"],
        ],
        check=True,
    )


def test_symlink(tmp_path: pathlib.Path):
    # Arrange
    target = tmp_path / "target"
    target.touch()
    link = tmp_path / "link"

    # Run
    mkloaders.symlink(target, link)

    # Assert
    assert link.exists()
    assert link.is_symlink()
    assert link.resolve() == target


def test_symlink_link_exists(tmp_path):
    # Arrange
    target = tmp_path / "target"
    target.touch()
    link = tmp_path / "link"
    link.touch()

    # Act
    with pytest.raises(FileExistsError):
        mkloaders.symlink(link, target, skip_existing=False)

    # Assert: must not raise an exception
    mkloaders.symlink(link, target, skip_existing=True)


def test_symlink_target_missing(tmp_path):
    # Arrange
    target = tmp_path / "target"
    link = tmp_path / "link"

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        mkloaders.symlink(target, link)


def test_get_syslinux_version():
    # Arrange & Act
    result = mkloaders.get_syslinux_version()

    # Assert
    assert result == 4
