#!/usr/bin/env -S bash -e

pacstrap /mnt base linux amd-ucode linux-firmware grub grub-btrfs snapper snap-pac efibootmgr sudo networkmanager apparmor python-psutil python-notify2 nano gnome gdm gnome-control-center gnome-terminal gnome-software gnome-software-packagekit-plugin gnome-tweaks nautilus pipewire-pulse pipewire-alsa pipewire-jack flatpak firewalld zram-generator adobe-source-han-sans-otc-fonts adobe-source-han-serif-otc-fonts gnu-free-fonts reflector mlocate man-db chrony dkms xorg-server xorg-xinit nvidia-dkms nvidia mesa xf86-video-amdgpu xf86-video-ati libva-mesa-driver vulkan-radeon
# Finishing up
echo "Done, you may now wish to reboot (further changes can be done by chrooting into /mnt)."
exit
