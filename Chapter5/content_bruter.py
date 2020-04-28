import urllib2 
import urllib
import threading
import Queue

threads        = 5
target_url     = "http://testphp.vulnweb.com"
wordlist_file  = "/tmp/all.txt" # from SVNDigger
resume         = None
user_agent     = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"

def build_wordlist(wordlist_file):

    # read in the word list
    fd = open(wordlist_file,"rb") 
    raw_words = fd.readlines()
    fd.close()
    
    found_resume = False
    words        = Queue.Queue()
    
    for word in raw_words:
        
        word = word.rstrip()
        
        if resume is not None:
            
            if found_resume:
                words.put(word)
            else:
                if word == resume:
                    found_resume = True
                    print "Resuming wordlist from: %s" % resume
                                        
        else:
            words.put(word)
    
    return words


def dir_bruter(extensions=None):
    
    while not word_queue.empty():
        attempt = word_queue.get()
        
        attempt_list = []
        
        # check if there is a file extension if not
        # it's a directory path we're bruting
        if "." not in attempt:
            attempt_list.append("/%s/" % attempt)
        else:
            attempt_list.append("/%s" % attempt)
    
        # if we want to bruteforce extensions
        if extensions:
            for extension in extensions:
                attempt_list.append("/%s%s" % (attempt,extension))
                
        # iterate over our list of attempts        
        for brute in attempt_list:
            
            url = "%s%s" % (target_url,urllib.quote(brute))
            
            try:
                headers = {}
                headers["User-Agent"] = user_agent
                r = urllib2.Request(url,headers=headers)
                
                
                response = urllib2.urlopen(r)
                
                if len(response.read()):
                    print "[%d] => %s" % (response.code,url)
                    
            except urllib2.HTTPError,e:

                if e.code != 404:
                    print "!!! %d => %s" % (e.code,url)
                
                pass


word_queue = build_wordlist(wordlist_file)
extensions = [".php",".bak",".orig",".inc"]

for i in range(threads):
            t = threading.Thread(target=dir_bruter,args=(extensions,))
            t.start()