import os, sys

if len(sys.argv) <= 1:
	print "no apt package provided"
	sys.exit()

workPath = os.getcwd()
appName = ''
appVersion = ''
igelBuild = '1'
appPath = ''
appFilesPath = ''
debPackage = ''
appSize = ''
initScriptPath = ''
infFilePath = ''


# Function for getting the unpacked folder size
def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return str((total_size/1024/1024)*1.5)


# Get application name
appName = raw_input('\033[95mEnter the application name: \033[0m')
if not appName:
	print "\033[91mError: no app name was given"
	sys.exit()
# Get application version
appVersion = raw_input('\033[95mEnter the application version: \033[0m')
if not appVersion:
        print "\033[91mError: no app version was given"
        sys.exit()
# Get igel build version
igelBuild = raw_input('\033[95mEnter the igel application build (optional, default: 1): \033[0m')
if not igelBuild:
	igelBuild = '1'
# Create application directory
print '\033[95mCreating application directory \033[92m-> \033[96m' + workPath + '/' + appName
appPath = workPath + '/' + appName
os.system('mkdir ' + appName)
appFilesPath = workPath + '/' + appName + '/' + appName.lower()
os.system('mkdir ' + appName + '/' + appName.lower())
# clear aptitude cache
os.system("aptitude clean")
# download package plus dependencies
aptCMD = 'sudo apt-get download '
aptCMD += '$(apt-cache depends --recurse --no-recommends --no-suggests --no-conflicts '
aptCMD += '--no-breaks --no-replaces --no-enhances --no-pre-depends ' + sys.argv[1] + ' | grep "^\w" | grep -v "i386")'
os.system(aptCMD)
os.system('mv ' + workPath + '/*.deb ' + appFilesPath + '/')
# Unpack deb package
print '\033[95mUnpacking .deb package(s)...'
packages = os.listdir(appFilesPath)
for pkg in packages:
	print 'unpack... ' + pkg
	os.system('dpkg -x ' + appFilesPath + '/' + pkg  +  ' ' + appFilesPath + '/')
# Get unpacked application size
appSize = get_size(appPath) + 'M'
# Get all .png files in this package
icons = [os.path.join(dp, f) for dp, dn, filenames in os.walk(appFilesPath) for f in filenames if os.path.splitext(f)[1] == '.png']


# Check package for binary
print '\033[95mChecking package for binaries...'
isBinary = False
binaryFile = ''
if os.path.exists(appFilesPath + '/usr/bin'):
	binaries = os.listdir(appFilesPath + '/usr/bin')
	if len(binaries) > 0:
		isBinary = True
		binaryFile = binaries[0]
		print '\033[95mfound -> \033[96m[' + binaryFile + ']'

# Create Igel init script
initScriptPath = appPath + '/custompart-' + appName.lower()
print '\033[95mCreating igel init script -> \033[96m' + initScriptPath
initScript = """
#!/bin/sh

ACTION="/custompart-""" + appName.lower() + """_${1}"

# mount point path
MP=$(get custom_partition.mountpoint)

# custom partition path
CP="${MP}/""" + appName.lower() + '"'

if isBinary:
	initScript = initScript + """
# only needed if application has an executable
BIN="/usr/bin/""" + binaryFile + '"'

initScript = initScript + """
# output to systemlog with ID amd tag
LOGGER="logger -it ${ACTION}"

echo "Starting" | $LOGGER

case "$1" in
init)
        # Linking files and folders on proper path
	find ${CP} | while read LINE
        do
                DEST=$(echo -n "${LINE}" | sed -e "s|${CP}||g")
                if [ ! -z "${DEST}" -a ! -e "${DEST}" ]; then
                        # Remove the last slash, if it is a dir
                        [ -d $LINE ] && DEST=$(echo "${DEST}" | sed -e "s/\/$//g") | $LOGGER
                        if [ ! -z "${DEST}" ]; then
                                ln -sv "${LINE}" "${DEST}" | $LOGGER
                        fi
                fi
        done
;;
stop)
        # unlink linked files
	    find ${CP} | while read LINE
            do
                DEST=$(echo -n "${LINE}" | sed -e "s|${CP}||g")
		    unlink $DEST | $LOGGER
	    done
;;
esac

echo "Finished" | $LOGGER

exit 0
"""
f = open(initScriptPath, 'w')
f.write(initScript)
f.close()


# make files executable
print '\033[95mMake files executable...'
os.system('chmod -R +x ' + appPath)
# compress files
print '\033[95mCompress files to .tar.bz2 archive...\033[96m'
os.system('cd ' + appPath  + '; tar cjvf ' + appName.lower() + '_' + appVersion + '.tar.bz2 ' + appName.lower() + ' custompart-' + appName.lower())
# clean up files
print '\033[95mClean up files...'
os.system('rm -rf ' + appFilesPath)
os.system('rm -rf ' + initScriptPath)
# create inf file
print '\033[95mCreating igel inf file...'
infFilePath = appPath + '/' + appName.lower() + '.inf'
infFile = []
infFile.append('[INFO]')
infFile.append('[PART]')
infFile.append('file="' + appName.lower() + '_' + appVersion + '.tar.bz2"')
infFile.append('version="' + appVersion + '_igel' + igelBuild + '"')
infFile.append('size="' + appSize + '"')
infFile.append('name="' + appName.lower() + '"')
infFile.append('minfw="11.01.100"')

with open(infFilePath, 'w') as f:
    for line in infFile:
        f.write("%s\n" % line)


# finish setup
f = open(appPath + '/README.md', 'w')
f.write('IGEL PACKAGE INFO\n')
f.write('==========================\n')
for line in infFile[2:]:
	f.write(line + '\n')
f.write('\nUMS Settings:\n')
f.write('==========================\n')
f.write('Initializing Action -> /"enter your mountpoint"/custompart-' + appName.lower() + ' init\n')
f.write('Finalizing Action -> /"enter your mountpoint"/custompart-' + appName.lower() + ' stop\n')
f.write('Command -> ' + binaryFile + '\n')
f.write('\nIcon Name(s):\n')
f.write('==========================\n')
for icon in icons:
        f.write(icon.replace(appFilesPath, '') + '\n')
f.write('\n\nFor more information about UMS settings see https://kb.igel.com/igelos-11.04/en/creating-a-profile-for-the-custom-partition-32868992.html')
f.close()

# set permissions
os.system('chmod -R a+rwx ' + workPath + '/' + appName)

print ''
print '\033[1m\033[92msetup successfully finished!'
print '\033[4m\033[1m\033[94mIGEL PACKAGE INFO'
for line in infFile[2:]:
	print '\033[0m\033[96m' + line

print '\033[92mInitializing Action -> \033[96m/"enter your mountpoint"/custompart-' + appName.lower() + ' init'
print '\033[92mFinalizing Action -> \033[96m/"enter your mountpoint"/custompart-' + appName.lower() + ' stop'
print '\033[92mCommand -> \033[96m' + binaryFile
print '\033[1m\033[92mIcon Name(s):'
for icon in icons:
	print '\033[96m' + icon.replace(appFilesPath, '')
