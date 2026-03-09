import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='agcd_masking',
    version='1.0.0',
    description='A Python package for masking AGCD data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Damien Irving',
    author_email='irving.damien@gmail.com',
    url='https://github.com/climate-innovation-hub/agcd-masking',
    packages=['agcd_masking'],
    zip_safe=False,
    install_requires=['regionmask', 'clisops', 'cmdline_provenance'],
    license='MIT License',
    include_package_data=True,
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',)
)