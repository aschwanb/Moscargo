#!/usr/bin/python

from flask import Flask
from flask import render_template, redirect
app = Flask(__name__)
from operator import itemgetter
from distutils.version import LooseVersion
import plistlib
import os

#set this to the base of your munki repo:
repo_base = os.environ.get('MOSCARGO_REPO') or '/Users/Shared/repo/'

# yup, stolen whole-heartedly from http://stackoverflow.com/a/22878816/743638
def get_key_watcher():
    keys_seen = set()
    def key_not_seen(unfiltered_prod_dict):
        key = unfiltered_prod_dict['distinct_name']
        if key in keys_seen:
            return False  # key is not new
        else:
            keys_seen.add(key)
            return True  # key seen for the first time
    return key_not_seen

def get_icon_url(installer_type, icon_name, name):
	joined_path = os.path.join(repo_base,'icons', name) + '.png'
	if installer_type== 'profile':
	    icon_url = 'static/mobileconfig.png'
	elif icon_name:
	    icon_url = os.path.join('static/icons/', icon_name).replace(' ', '%20')
	elif os.path.exists(joined_path):
	    icon_url = os.path.join(repo_base, 'icons', name + '.png').replace(' ', '%20')
	else:
	    icon_url = 'static/package.png'
	return icon_url

def read_catalog(catalog_to_parse):
	try:
	    products = plistlib.readPlist(os.path.join(repo_base, 'catalogs', catalog_to_parse))
	    prodlist = []
	    for prod_dict in products:
		if not prod_dict.get('installer_type') == 'apple_update_metadata':
		    if not prod_dict.get('installer_type') == 'nopkg':
			joined_path = os.path.join(repo_base,'icons', prod_dict.get('name')) + '.png'
			this_prod_dict = {}
			try_keys = [('Name', 'display_name'), ('distinct_name', 'name')]
			for item in try_keys:
			    try:
				this_prod_dict[item[0]] = prod_dict.get(item[1])
			    except Exception:
				this_prod_dict[item[0]] = 'No %s found' % item[0]
			try:
			    this_prod_dict['version'] = LooseVersion(prod_dict.get('version'))
			except Exception:
			    this_prod_dict['description'] = 'No description found'
			try:
			    this_prod_dict['description'] = (prod_dict.get('description'))[:130] + '...'
			except Exception:
			    this_prod_dict['description'] = 'No description found'
			try:
			    this_prod_dict['link'] = (os.path.join('static/pkgs', prod_dict.get('installer_item_location'))).replace(' ', '%20')
			except Exception:
			    this_prod_dict['link'] = 'No link!'
			this_prod_dict['icon_url'] = get_icon_url(prod_dict.get('installer_type'),
								  prod_dict.get('icon_name'),
								  prod_dict.get('name'))
			prodlist.append(this_prod_dict)
	    listbyvers = sorted(prodlist, key=itemgetter('version'), reverse=True)
	    filtered = filter(get_key_watcher(), listbyvers)
	    sprodlist = sorted(filtered, key=itemgetter('Name'))
	    return sprodlist

	except Exception, e:
	    print e

@app.route('/')
@app.route('/<catalog>')
def index(catalog="production"):
	if not catalog == "testing" and not catalog == "production":
		catalog = "production"
	sprodlist = read_catalog(catalog)
	return render_template('moscargo.html', example_prods=sprodlist, catalog=catalog)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
