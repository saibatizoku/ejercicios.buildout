# -*- coding: utf-8 -*-
import math
from five import grok
from zope import schema
from zope.interface import Interface

from Products.CMFPlone.utils import getToolByName
from plone.directives import form, dexterity
from plone.app.textfield import RichText
from plone.app.layout.viewlets.interfaces import IAboveContentBody
from plone.app.layout.viewlets.interfaces import IHtmlHeadLinks

from collective.nitf import _
from collective.nitf import INITFBrowserLayer
from collective.nitf.config import PROPERTIES, URGENCIES, NORMAL

VIDEO_MIMETYPES = ['video/mp4', 'video/x-flv']
IMAGE_MIMETYPES = ['image/jpeg', 'image/gif', 'image/png']

class INITF(form.Schema):
    """A news item based on the News Industry Text Format specification.
    """

    body = RichText(
            title=_(u'Body text'),
            required=False,
            default=u'',
        )

    property_ = schema.Choice(
            title=_(u'Property'),
            vocabulary=PROPERTIES,
            default='Current',
        )

    section = schema.Text(
            title=_(u'Section'),
            required=False,
            default=u'',
        )

    urgency = schema.Choice(
            title=_(u'Urgency'),
            vocabulary=URGENCIES,
            default=NORMAL,
        )

    byline = schema.Text(
            title=_(u'Author'),
            required=False,
            default=u'',
        )


class IMediaView(Interface):
    """ Marker view for media views"""


class Media_View(grok.View):
    grok.context(INITF)
    grok.implements(IMediaView)
    grok.name('media_view')
    grok.title(u'Media View')
    grok.require('zope2.View')

    def update(self):
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.get_images()

    def get_images(self):
        return self.get_media_files(types=('Image',))

    def get_videos(self):
        return self.get_media_files(types=('File',))

    def get_media_files(self, types=('Image', 'File',)):
        context_path = '/'.join(self.context.getPhysicalPath())
        media_brains = self.catalog.searchResults(
                        {'Type': types,
                         'path': {'query': context_path,
                                  'depth': 1},
                         },
                        sort_on="getObjPositionInParent")
        media_items = []
        for brain in media_brains:
            ibrain = { 'id': brain.id,
                       'title': brain.Title,
                       'image_url': brain.getURL(),
                       }
            if brain.getObject().getContentType() in IMAGE_MIMETYPES:
                ibrain['media_type'] = 'image'
            elif brain.getObject().getContentType() in VIDEO_MIMETYPES:
                ibrain['media_type'] = 'video'
            else:
                ibrain['media_type'] = None
            media_items.append(ibrain)
        return media_items


class NewsItem_View(Media_View):
    grok.implements(IMediaView)
    grok.name('newsitem_view')
    grok.require('zope2.View')
    grok.layer(INITFBrowserLayer)


class MediaViewletManager(grok.ViewletManager):
    grok.context(INITF)
    grok.name('collective.nitf.carousel')
    grok.view(Media_View)
    grok.layer(INITFBrowserLayer)


class MediaViewlet(grok.Viewlet):
    grok.context(INITF)
    grok.name('collective.nitf.media.tile')
    grok.viewletmanager(IAboveContentBody)
    grok.view(NewsItem_View)
    grok.template('media_viewlet')
    grok.require('zope2.View')
    grok.layer(INITFBrowserLayer)
   
    image_size = 'tile'

    def update(self, image_size=None):
        if image_size is not None:
            self.image_size = image_size
        self.media_name = "media-%s" % self.image_size

    def mediaRows(self, keys, cols='5'):
        rows = []
        if not cols or not keys:
            return rows
        rows_number = int(math.ceil(float(len(keys)) / float(cols)))
        for row in range(rows_number):
            this_row = []
            start = row * int(cols)
            end = start + int(cols)
            for key in keys[start:end]:
                this_row.append(key)
            rows.append(this_row)
        return rows


class MediaPreviewViewlet(MediaViewlet):
    grok.name('collective.nitf.media.preview')
    grok.viewletmanager(MediaViewletManager)
    grok.view(Media_View)
    grok.layer(INITFBrowserLayer)

    image_size = 'preview'


class MediaLinksViewlet(grok.Viewlet):
    grok.context(INITF)
    grok.name('collective.nitf.links.media')
    grok.template('media_links')
    grok.viewletmanager(IHtmlHeadLinks)
    grok.view(IMediaView)
    grok.layer(INITFBrowserLayer)
