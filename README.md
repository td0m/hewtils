# Hewtils
> Utility library

## Scripts

To install scripts into your bin folder, simply run:
```bash
python install.py
```

Note that this requires you to either add `~/.local/bin` to path, or specify a custom bin path (e.g. `sudo python install.py /usr/bin`). This will simply copy all scripts to that directory without their `.py` extension.

### Clone

If you ever needed to quickly clone 3rd party git repositories or simply structure your current repositories, you'll definitely find this utility useful.

This utility allows you to automatically organise your repositories by their domain names, then owners, and then the repository names:

```
Git/
    github.com/
        td0m/
            hewtils
            dragons
            q
        facebook/
            react
```

You can clone repositories as easily as:
```bash
clone github.com/td0m/hewtils
```

You can also set a default domain name and clone other repositories without having to specify the domain name (this case `github.com`):
```bash
clone facebook/react
```

Or specify your default username and clone your own repositories such:
```bash
clone hewtils
```

## Snippets

### Always git clone with ssh keys

This will rewrite all your https git urls to use ssh. Useful if you are always prompted for credentials in the terminal, as it will use your ssh keys instead.

```bash
git config --global url.ssh://git@github.com/.insteadOf https://github.com/
```

### Clean downloads folder on reboot

A great way to force yourself to organise your downloads is deleting the `Downloads/` folder regularly. The following cronjob (add via `crontab -e`) will remove all files in the downloads directory on reboot:

```
@reboot gio trash $HOME/Downloads/*
```
Or if you don't use the trash folder:
```
@reboot rm -rf $HOME/Downloads/*
```

### Add 'Open in VsCode' to Nautilus context menu

```bash
wget -qO- https://raw.githubusercontent.com/harry-cpp/code-nautilus/master/install.sh | bash
```