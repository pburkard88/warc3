warc3: Python3 library to work with WARC files
=============================================

(Note: This is a fork of the original (now dead) warc repository. This is a rough python3 port / update that I used in my warc-extractor located here https://github.com/recrm/ArchiveTools. As the tool is complete, I have mostly stopped development of this library.)

.. image:: https://secure.travis-ci.org/anandology/warc.png?branch=master
   :alt: build status
   :target: http://travis-ci.org/anandology/warc

WARC (Web ARChive) is a file format for storing web crawls.

http://bibnum.bnf.fr/WARC/ 

This `warc` library makes it very easy to work with WARC files.::

    import warc
    with warc.open("test.warc") as f:
        for record in f:
            print record['WARC-Target-URI'], record['Content-Length']

Documentation
-------------

The documentation of the warc library is available at http://warc.readthedocs.org/.
	
License
-------

This software is licensed under GPL v2. See LICENSE_ file for details.

.. LICENSE: http://github.com/internetarchive/warc/blob/master/LICENSE
