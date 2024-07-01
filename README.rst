dlrfp
=========

dlrfp is a simple (and dirty) web scraping script for Radio France podcasts.

The project aims to create a quick and dirty but usable RSS feed for a given radio programme.

Basically done in 3 steps :

- Crawl through each page of a programme and put each of them in a list
- From this list, get all episodes links
- Crawling through the list to get each episode's necessary information and add these to an RSS XML file.

Side comment, you can use yt-dlp if you put the list of episodes in a file with something like this:
    ``yt-dlp --extract-audio -o '%(upload_date)s - %(title)s' -a url_podcast.txt``

You can find some examples with the podcast 'Sur les épaules de Darwin' in 'example/'. It's also the only one radio programme tested. It may work on other from Radio France.

I quickly cleaned some escaped characters but there would probably remain some left.

Dependencies
--------------------

Nothing except Python 3 and modules from the standard library.

License
----------

dlrfp is licensed under `the MIT/Expat License
<https://spdx.org/licenses/MIT.html>`_. See LICENSE file for details.

