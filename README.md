JPyReader
=========

Lightweight image viewer aimed at manga/comics.<br>

<h2>How to install</h2>

JPyReader doesn't really require "installing". It is portable by nature.<br>
In order to get JPyReader running, however, you must first install Python and wxPython.<br>
<br>
If you are running a linux operating system, Python is likely already installed on your system.<br>
If it isn't, you should use your distribution's package manager to install Python rather than downloading it from the link provided.<br>
The same goes for wxPython. Although less likely to be installed by default, you should first check if it's available in your distribution's package manager.<br>On Ubuntu derivatives, the package name may be something along the lines of "python-wxgtk2.8".<br>
<br>
If the above doesn't apply to you, Python can be found here: https://www.python.org/download/releases/2.7.6/ <br>
At the time of writing, 2.7.6 is the latest version of Python in the 2.x branch.<br>
JPyReader is not currently compatible with Python 3.x.<br>
<br>
wxPython can be found here: http://www.wxpython.org/download.php#stable<br>
At the time of writing, 2.8.12.1 is the latest stable version of wxPython.<br>
<br>
In both cases, newer versions of the 2.x branch will likely work.<br>
Similarly, recent previous versions of the 2.x branch will also likely work.

<h2>Supported formats</h2>

Supported image formats: .png, .jpg, .jpeg, .gif, .bmp<br>
Supported archive formats: .zip, .cbz, .rar, .cbr<br>
<br>
All supported archive formats can be read in three ways:
<ul>
<li>extracted to your temp directory, then the individual files are read like normal (default)</li>
<li>accessed directly from the archive one image at a time</li>
<li>extracted directly and completely into RAM</li>
</ul>
Option 1 is the default and usually the most fool-proof/safest bet. Caching of the previous and next image is supported.<br>
Option 2 removes the need for extracting the archive's contents to disk, and only loads the viewed image into RAM. This option is the most balanced, and is preferable for people who don't want unnecessary disk IO (eg. on SSDs).<br>
Option 3 is the slowest to start, but the fastest once loaded. It requires more RAM than the other two options, but may be preferably if you flip from page to page very quickly, or you read the same pages multiple times.<br>

<h2>License</h2>

Distributed under the MIT license: http://opensource.org/licenses/MIT<br>
Explained in plain English: https://tldrlegal.com/license/mit-license<br>
The rar parsing library included comes with its own license included in the rarfile directory.<br>
