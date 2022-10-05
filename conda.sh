__conda_setup="$('/g/data/wp00/users/dbi599/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/g/data/wp00/users/dbi599/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/g/data/wp00/users/dbi599/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/g/data/wp00/users/dbi599/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup