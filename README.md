# Deb2Igel

Convert ubuntu software packages (+dependencies) to igel packages


To install software packages on ubuntu you would normally use APT-GET like:<br>
`sudo apt-get install {packageName}`

The problem with IGEL OS is, that there is no package manager.
Therefore IGEL introduced the custom partitions to install additional software. (see https://kb.igel.com/igelos-11.04/en/custom-partition-tutorial-32868832.html)
Deb2Igel aims to reduce the efforts to create such packages for custom partitions.

# Usage
Example:<br>
Create a package with dependencies to install "make" on IGEL OS<br>
`sudo python deb2igel.py make`

Syntax:<br>
`sudo python deb2igel.py {apt-get package name}`
