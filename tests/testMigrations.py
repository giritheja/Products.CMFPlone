#
# Tests for migration components
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.CMFPlone.tests import PloneTestCase

from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.interfaces import IActionCategory
from Products.CMFCore.interfaces import IActionInfo
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFPlone.PloneTool import AllowSendto
from Products.CMFPlone.interfaces import IControlPanel
from Products.CMFPlone.interfaces import IInterfaceTool
from Products.CMFPlone.interfaces import IMigrationTool
from Products.CMFPlone.interfaces import ITranslationServiceTool
from Products.CMFPlone.utils import _createObjectByType
from Products.CMFPlone.UnicodeSplitter import Splitter, CaseNormalizer

from Products.CMFPlone.migrations.v2_1.final_two11 import reindexPathIndex
from Products.CMFPlone.migrations.v2_1.two11_two12 import removeCMFTopicSkinLayer
from Products.CMFPlone.migrations.v2_1.two11_two12 import addRenameObjectButton
from Products.CMFPlone.migrations.v2_1.two11_two12 import addSEHighLightJS
from Products.CMFPlone.migrations.v2_1.two11_two12 import removeDiscussionItemWorkflow
from Products.CMFPlone.migrations.v2_1.two11_two12 import addMemberData
from Products.CMFPlone.migrations.v2_1.two11_two12 import reinstallPortalTransforms

from Products.CMFPlone.migrations.v2_1.two12_two13 import normalizeNavtreeProperties
from Products.CMFPlone.migrations.v2_1.two12_two13 import removeVcXMLRPC
from Products.CMFPlone.migrations.v2_1.two12_two13 import addActionDropDownMenuIcons

from Products.CMFPlone.migrations.v2_5.alphas import installPlacefulWorkflow
from Products.CMFPlone.migrations.v2_5.alphas import installDeprecated
from Products.CMFPlone.migrations.v2_5.alphas import installPlonePAS

from Products.CMFPlone.migrations.v2_5.betas import addGetEventTypeIndex
from Products.CMFPlone.migrations.v2_5.betas import fixHomeAction
from Products.CMFPlone.migrations.v2_5.betas import removeBogusSkin
from Products.CMFPlone.migrations.v2_5.betas import addPloneSkinLayers
from Products.CMFPlone.migrations.v2_5.betas import installPortalSetup
from Products.CMFPlone.migrations.v2_5.betas import simplifyActions
from Products.CMFPlone.migrations.v2_5.betas import migrateCSSRegExpression

from Products.CMFPlone.migrations.v2_5.final_two51 import removePloneCssFromRR
from Products.CMFPlone.migrations.v2_5.final_two51 import addEventRegistrationJS
from Products.CMFPlone.migrations.v2_5.final_two51 import fixupPloneLexicon
from Products.CMFPlone.migrations.v2_5.final_two51 import fixObjDeleteAction

from Products.CMFPlone.migrations.v2_5.two51_two52 import setLoginFormInCookieAuth

from Products.CMFPlone.migrations.v3_0.alphas import enableZope3Site
from Products.CMFPlone.migrations.v3_0.alphas import migrateOldActions
from Products.CMFPlone.migrations.v3_0.alphas import addNewCSSFiles
from Products.CMFPlone.migrations.v3_0.alphas import addDefaultAndForbiddenContentTypesProperties
from Products.CMFPlone.migrations.v3_0.alphas import addTypesConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import updateActionsI18NDomain
from Products.CMFPlone.migrations.v3_0.alphas import updateFTII18NDomain
from Products.CMFPlone.migrations.v3_0.alphas import convertLegacyPortlets
from Products.CMFPlone.migrations.v3_0.alphas import addIconForCalendarSettingsConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import addIconForMaintenanceConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import addCalendarConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import addMaintenanceConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import updateSearchAndMailHostConfiglet
from Products.CMFPlone.migrations.v3_0.alphas import addFormTabbingJS
from Products.CMFPlone.migrations.v3_0.alphas import addFormInputLabelJS
from Products.CMFPlone.migrations.v3_0.alphas import registerToolsAsUtilities
from Products.CMFPlone.migrations.v3_0.alphas import installKss
from Products.CMFPlone.migrations.v3_0.alphas import installRedirectorUtility
from Products.CMFPlone.migrations.v3_0.alphas import addContentRulesAction
from Products.CMFPlone.migrations.v3_0.alphas import addReaderAndEditorRoles
from Products.CMFPlone.migrations.v3_0.alphas import migrateLocalroleForm
from Products.CMFPlone.migrations.v3_0.alphas import reorderUserActions
from Products.CMFPlone.migrations.v3_0.alphas import updateRtlCSSexpression
from Products.CMFPlone.migrations.v3_0.alphas import addMaintenanceProperty
from Products.CMFPlone.migrations.v3_0.alphas import installS5
from Products.CMFPlone.migrations.v3_0.alphas import addTableContents
from Products.CMFPlone.migrations.v3_0.alphas import updateMemberSecurity

from zope.app.component.hooks import clearSite
from zope.app.component.interfaces import ISite
from zope.component import getGlobalSiteManager
from zope.component import getSiteManager

from zope.component import getUtility, getMultiAdapter

from Products.CMFDynamicViewFTI.migrate import migrateFTI
from Products.Five.component import disableSite

import types
from Acquisition import aq_base

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import CONTEXT_CATEGORY as CONTEXT_PORTLETS
from plone.app.portlets import portlets

from plone.app.redirector.interfaces import IRedirectionStorage

class BogusMailHost(SimpleItem):
    meta_type = 'Bad Mailer'
    title = 'Mailer'
    smtp_port = 37
    smtp_host = 'my.badhost.com'


class MigrationTest(PloneTestCase.PloneTestCase):

    def removeActionFromTool(self, action_id, category=None, action_provider='portal_actions'):
        # Removes an action from portal_actions
        tool = getattr(self.portal, action_provider)
        if category is None:
            if action_id in tool.objectIds() and IActionInfo.providedBy(tool._getOb(action_id)):
                tool._delOb(action_id)
        else:
            if category in tool.objectIds() and IActionCategory.providedBy(tool._getOb(category)):
                if action_id in tool.objectIds() and IActionInfo.providedBy(tool._getOb(action_id)):
                    tool._delOb(action_id)

    def removeActionIconFromTool(self, action_id, category='plone'):
        # Removes an action icon from portal_actionicons
        tool = getattr(self.portal, 'portal_actionicons')
        try:
            tool.removeActionIcon(category, action_id)
        except KeyError:
            pass # No icon associated

    def addResourceToJSTool(self, resource_name):
        # Registers a resource with the javascripts tool
        tool = getattr(self.portal, 'portal_javascripts')
        if not resource_name in tool.getResourceIds():
            tool.registerScript(resource_name)

    def addResourceToCSSTool(self, resource_name):
        # Registers a resource with the css tool
        tool = getattr(self.portal, 'portal_css')
        if not resource_name in tool.getResourceIds():
            tool.registerStylesheet(resource_name)

    def removeSiteProperty(self, property_id):
        # Removes a site property from portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])

    def addSiteProperty(self, property_id):
        # adds a site property to portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        if not sheet.hasProperty(property_id):
            sheet.manage_addProperty(property_id,[],'lines')

    def removeNavTreeProperty(self, property_id):
        # Removes a navtree property from portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'navtree_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])

    def addNavTreeProperty(self, property_id):
        # adds a navtree property to portal_properties
        tool = getattr(self.portal, 'portal_properties')
        sheet = getattr(tool, 'navtree_properties')
        if not sheet.hasProperty(property_id):
            sheet.manage_addProperty(property_id,[],'lines')

    def removeMemberdataProperty(self, property_id):
        # Removes a memberdata property from portal_memberdata
        tool = getattr(self.portal, 'portal_memberdata')
        if tool.hasProperty(property_id):
            tool.manage_delProperties([property_id])

    def uninstallProduct(self, product_name):
        # Removes a product
        tool = getattr(self.portal, 'portal_quickinstaller')
        if tool.isProductInstalled(product_name):
            tool.uninstallProducts([product_name])

    def addSkinLayer(self, layer, skin='Plone Default', pos=None):
        # Adds a skin layer at pos. If pos is None, the layer is appended
        path = self.skins.getSkinPath(skin)
        path = [x.strip() for x in path.split(',')]
        if layer in path:
            path.remove(layer)
        if pos is None:
            path.append(layer)
        else:
            path.insert(pos, layer)
        self.skins.addSkinSelection(skin, ','.join(path))

    def removeSkinLayer(self, layer, skin='Plone Default'):
        # Removes a skin layer from skin
        path = self.skins.getSkinPath(skin)
        path = [x.strip() for x in path.split(',')]
        if layer in path:
            path.remove(layer)
            self.skins.addSkinSelection(skin, ','.join(path))


class TestMigrations_v2_1_1(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.icons = self.portal.portal_actionicons
        self.properties = self.portal.portal_properties
        self.memberdata = self.portal.portal_memberdata
        self.membership = self.portal.portal_membership
        self.catalog = self.portal.portal_catalog
        self.groups = self.portal.portal_groups
        self.factory = self.portal.portal_factory
        self.portal_memberdata = self.portal.portal_memberdata
        self.cp = getUtility(IControlPanel)
        self.skins = self.portal.portal_skins

    def testReindexPathIndex(self):
        # Should reindex the path index to create new index structures
        orig_results = self.catalog(path={'query':'news', 'level':1})
        orig_len = len(orig_results)
        self.failUnless(orig_len)
        # Simulate the old EPI
        delattr(self.catalog.Indexes['path'], '_index_parents')
        self.assertRaises(AttributeError, self.catalog,
                                        {'path':{'query':'/','navtree':1}})
        reindexPathIndex(self.portal, [])
        results = self.catalog(path={'query':'news', 'level':1})
        self.assertEqual(len(results), orig_len)

    def testReindexPathIndexTwice(self):
        # Should not fail when migrated twice, should do nothing if already
        # migrated
        orig_results = self.catalog(path={'query':'news', 'level':1})
        orig_len = len(orig_results)
        self.failUnless(orig_len)
        # Simulate the old EPI
        delattr(self.catalog.Indexes['path'], '_index_parents')
        self.assertRaises(AttributeError, self.catalog,
                                        {'path':{'query':'/','navtree':1}})
        out = []
        reindexPathIndex(self.portal, out)
        # Should return a message on the first iteration
        self.failUnless(out)
        out = []
        reindexPathIndex(self.portal, out)
        results = self.catalog(path={'query':'news', 'level':1})
        self.assertEqual(len(results), orig_len)
        # should return an empty list on the second iteration because nothing
        # was done
        self.failIf(out)

    def testReindexPathIndexNoIndex(self):
        # Should not fail when index is missing
        self.catalog.delIndex('path')
        reindexPathIndex(self.portal, [])

    def testReindexPathIndexNoCatalog(self):
        # Should not fail when index is missing
        self.portal._delObject('portal_catalog')
        reindexPathIndex(self.portal, [])


class TestMigrations_v2_1_2(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.memberdata = self.portal.portal_memberdata
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow

    def testRemoveCMFTopicSkinPathFromDefault(self):
        # Should remove plone_3rdParty/CMFTopic from skin paths
        self.addSkinLayer('plone_3rdParty/CMFTopic')
        removeCMFTopicSkinLayer(self.portal, [])
        path = self.skins.getSkinPath('Plone Default')
        self.failIf('plone_3rdParty/CMFTopic' in path)

    def testRemoveCMFTopicSkinPathFromTableless(self):
        # Should remove plone_3rdParty/CMFTopic from skin paths
        self.addSkinLayer('plone_3rdParty/CMFTopic', skin='Plone Tableless')
        removeCMFTopicSkinLayer(self.portal, [])
        path = self.skins.getSkinPath('Plone Tableless')
        self.failIf('plone_3rdParty/CMFTopic' in path)

    def testRemoveCMFTopicSkinTwice(self):
        # Should not fail if migrated again
        self.addSkinLayer('plone_3rdParty/CMFTopic')
        removeCMFTopicSkinLayer(self.portal, [])
        removeCMFTopicSkinLayer(self.portal, [])
        path = self.skins.getSkinPath('Plone Default')
        self.failIf('plone_3rdParty/CMFTopic' in path)

    def testRemoveCMFTopicSkinNoTool(self):
        # Should not fail if tool is missing
        self.portal._delObject('portal_skins')
        removeCMFTopicSkinLayer(self.portal, [])

    def testRemoveCMFTopicSkinPathNoLayer(self):
        # Should not fail if plone_3rdParty layer is missing
        self.removeSkinLayer('plone_3rdParty')
        removeCMFTopicSkinLayer(self.portal, [])
        path = self.skins.getSkinPath('Plone Default')
        self.failIf('plone_3rdParty/CMFTopic' in path)

    def testAddRenameObjectButton(self):
        # Should add 'rename' object_button action
        editActions = self.actions.object_buttons.objectIds()
        assert 'rename' in editActions
        self.removeActionFromTool('rename', 'object_buttons')
        addRenameObjectButton(self.portal, [])
        actions = self.actions.object_buttons.objectIds()
        self.assertEqual(sorted(actions), sorted(editActions))

    def testAddRenameObjectButtonTwice(self):
        # Should not fail if migrated again
        editActions = self.actions.object_buttons.objectIds()
        assert 'rename' in editActions
        self.removeActionFromTool('rename', 'object_buttons')
        addRenameObjectButton(self.portal, [])
        addRenameObjectButton(self.portal, [])
        actions = self.actions.object_buttons.objectIds()
        self.assertEqual(sorted(actions), sorted(editActions))

    def testAddRenameObjectButtonActionExists(self):
        # Should add 'rename' object_button action
        editActions = self.actions.object_buttons.objectIds()
        assert 'rename' in editActions
        addRenameObjectButton(self.portal, [])
        actions = self.actions.object_buttons.objectIds()
        self.assertEqual(sorted(actions), sorted(editActions))

    def testAddRenameObjectButtonNoTool(self):
        # Should not fail if tool is missing
        self.portal._delObject('portal_actions')
        addRenameObjectButton(self.portal, [])

    def testAddSEHighLightJS(self):
        jsreg = self.portal.portal_javascripts
        script_ids = jsreg.getResourceIds()
        self.failUnless('se-highlight.js' in script_ids)
        # if highlightsearchterms.js is available se-highlight.js
        # should be positioned right underneath it
        if 'highlightsearchterms.js' in script_ids:
            posSE = jsreg.getResourcePosition('se-highlight.js')
            posHST = jsreg.getResourcePosition('highlightsearchterms.js')
            self.failUnless((posSE - 1) == posHST)

    def testRemoveDiscussionItemWorkflow(self):
        self.workflow.setChainForPortalTypes(('Discussion Item',), ('(Default)',))
        removeDiscussionItemWorkflow(self.portal, [])
        self.assertEqual(self.workflow.getChainForPortalType('Discussion Item'), ())

    def testRemoveDiscussionItemWorkflowNoTool(self):
        self.portal._delObject('portal_workflow')
        removeDiscussionItemWorkflow(self.portal, [])

    def testRemoveDiscussionItemWorkflowNoType(self):
        self.types._delObject('Discussion Item')
        removeDiscussionItemWorkflow(self.portal, [])

    def testRemoveDiscussionItemWorkflowTwice(self):
        self.workflow.setChainForPortalTypes(('Discussion Item',), ('(Default)',))
        removeDiscussionItemWorkflow(self.portal, [])
        self.assertEqual(self.workflow.getChainForPortalType('Discussion Item'), ())
        removeDiscussionItemWorkflow(self.portal, [])
        self.assertEqual(self.workflow.getChainForPortalType('Discussion Item'), ())

    def testAddMustChangePassword(self):
        # Should add the 'must change password' property
        self.removeMemberdataProperty('must_change_password')
        self.failIf(self.memberdata.hasProperty('must_change_password'))
        addMemberData(self.portal, [])
        self.failUnless(self.memberdata.hasProperty('must_change_password'))

    def testAddMustChangePasswordTwice(self):
        # Should not fail if migrated again
        self.removeMemberdataProperty('must_change_password')
        self.failIf(self.memberdata.hasProperty('must_change_password'))
        addMemberData(self.portal, [])
        addMemberData(self.portal, [])
        self.failUnless(self.memberdata.hasProperty('must_change_password'))

    def testAddMustChangePasswordNoTool(self):
        # Should not fail if portal_memberdata is missing
        self.portal._delObject('portal_memberdata')
        addMemberData(self.portal, [])

    def testReinstallPortalTransforms(self):
        self.portal._delObject('portal_transforms')
        reinstallPortalTransforms(self.portal, [])
        self.failUnless(hasattr(self.portal.aq_base, 'portal_transforms'))

    def testReinstallPortalTransformsTwice(self):
        self.portal._delObject('portal_transforms')
        reinstallPortalTransforms(self.portal, [])
        reinstallPortalTransforms(self.portal, [])
        self.failUnless(hasattr(self.portal.aq_base, 'portal_transforms'))

    def testReinstallPortalTransformsNoTool(self):
        self.portal._delObject('portal_quickinstaller')
        reinstallPortalTransforms(self.portal, [])


class TestMigrations_v2_1_3(MigrationTest):

    def testNormalizeNavtreeProperties(self):
        ntp = self.portal.portal_properties.navtree_properties
        toRemove = ['skipIndex_html', 'showMyUserFolderOnly', 'showFolderishSiblingsOnly',
                    'showFolderishChildrenOnly', 'showNonFolderishObject', 'showTopicResults',
                    'rolesSeeContentView', 'rolesSeeUnpublishedContent', 'batchSize',
                    'croppingLength', 'forceParentsInBatch', 'rolesSeeHiddenContent', 'typesLinkToFolderContents']
        toAdd = {'name' : '', 'root' : '/', 'currentFolderOnlyInNavtree' : False}
        for property in toRemove:
            ntp._setProperty(property, 'X', 'string')
        for property, value in toAdd.items():
            ntp._delProperty(property)
        ntp.manage_changeProperties(bottomLevel = 65535)
        normalizeNavtreeProperties(self.portal, [])
        for property in toRemove:
            self.assertEqual(ntp.getProperty(property, None), None)
        for property, value in toAdd.items():
            self.assertEqual(ntp.getProperty(property), value)
        self.assertEqual(ntp.getProperty('bottomLevel'), 0)

    def testNormalizeNavtreePropertiesTwice(self):
        ntp = self.portal.portal_properties.navtree_properties
        toRemove = ['skipIndex_html', 'showMyUserFolderOnly', 'showFolderishSiblingsOnly',
                    'showFolderishChildrenOnly', 'showNonFolderishObject', 'showTopicResults',
                    'rolesSeeContentView', 'rolesSeeUnpublishedContent', 'rolesSeeContentsView',
                    'batchSize', 'sortCriteria', 'croppingLength', 'forceParentsInBatch',
                    'rolesSeeHiddenContent', 'typesLinkToFolderContents']
        toAdd = {'name' : '', 'root' : '/', 'currentFolderOnlyInNavtree' : False}
        for property in toRemove:
            ntp._setProperty(property, 'X', 'string')
        for property, value in toAdd.items():
            ntp._delProperty(property)
        ntp.manage_changeProperties(bottomLevel = 65535)
        normalizeNavtreeProperties(self.portal, [])
        normalizeNavtreeProperties(self.portal, [])
        for property in toRemove:
            self.assertEqual(ntp.getProperty(property, None), None)
        for property, value in toAdd.items():
            self.assertEqual(ntp.getProperty(property), value)
        self.assertEqual(ntp.getProperty('bottomLevel'), 0)

    def testNormalizeNavtreePropertiesNoTool(self):
        self.portal._delObject('portal_properties')
        normalizeNavtreeProperties(self.portal, [])

    def testNormalizeNavtreePropertiesNoSheet(self):
        self.portal.portal_properties._delObject('navtree_properties')
        normalizeNavtreeProperties(self.portal, [])

    def testNormalizeNavtreePropertiesNoPropertyToRemove(self):
        ntp = self.portal.portal_properties.navtree_properties
        if ntp.getProperty('skipIndex_html', None) is not None:
            ntp._delProperty('skipIndex_html')
        normalizeNavtreeProperties(self.portal, [])

    def testNormalizeNavtreePropertiesNewPropertyExists(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root = '/foo', bottomLevel = 10)
        normalizeNavtreeProperties(self.portal, [])
        self.assertEqual(ntp.getProperty('root'), '/foo')
        self.assertEqual(ntp.getProperty('bottomLevel'), 10)

    def testRemoveVcXMLRPC(self):
        # Should unregister vcXMLRPC.js
        self.addResourceToJSTool('vcXMLRPC.js')
        removeVcXMLRPC(self.portal, [])
        jsreg = self.portal.portal_javascripts
        script_ids = jsreg.getResourceIds()
        self.failIf('vcXMLRPC.js' in script_ids)

    def testRemoveVcXMLRPCTwice(self):
        # Should not fail if migrated again
        self.addResourceToJSTool('vcXMLRPC.js')
        removeVcXMLRPC(self.portal, [])
        removeVcXMLRPC(self.portal, [])
        jsreg = self.portal.portal_javascripts
        script_ids = jsreg.getResourceIds()
        self.failIf('vcXMLRPC.js' in script_ids)

    def testRemoveVcXMLRPCNoTool(self):
        # Should not break if javascripts tool is missing
        self.portal._delObject('portal_javascripts')
        removeVcXMLRPC(self.portal, [])

    def testAddActionDropDownMenuIcons(self):
        # Should add icons to object buttons
        self.removeActionIconFromTool('cut', 'object_buttons')
        self.removeActionIconFromTool('copy', 'object_buttons')
        self.removeActionIconFromTool('paste', 'object_buttons')
        self.removeActionIconFromTool('delete', 'object_buttons')
        addActionDropDownMenuIcons(self.portal, [])
        ai=self.portal.portal_actionicons
        icons = dict([
            ((x.getCategory(), x.getActionId()), x)
            for x in ai.listActionIcons()
        ])
        self.failIf(('object_buttons', 'cut') not in icons)
        self.failIf(('object_buttons', 'copy') not in icons)
        self.failIf(('object_buttons', 'paste') not in icons)
        self.failIf(('object_buttons', 'delete') not in icons)
        self.assertEqual(icons[('object_buttons', 'cut')].getExpression(), 'cut_icon.gif')
        self.assertEqual(icons[('object_buttons', 'copy')].getExpression(), 'copy_icon.gif')
        self.assertEqual(icons[('object_buttons', 'paste')].getExpression(), 'paste_icon.gif')
        self.assertEqual(icons[('object_buttons', 'delete')].getExpression(), 'delete_icon.gif')
        self.assertEqual(icons[('object_buttons', 'cut')].getTitle(), 'Cut')
        self.assertEqual(icons[('object_buttons', 'copy')].getTitle(), 'Copy')
        self.assertEqual(icons[('object_buttons', 'paste')].getTitle(), 'Paste')
        self.assertEqual(icons[('object_buttons', 'delete')].getTitle(), 'Delete')

    def testAddActionDropDownMenuIconsTwice(self):
        # Should not fail if migrated again
        self.removeActionIconFromTool('cut', 'object_buttons')
        self.removeActionIconFromTool('copy', 'object_buttons')
        self.removeActionIconFromTool('paste', 'object_buttons')
        self.removeActionIconFromTool('delete', 'object_buttons')
        addActionDropDownMenuIcons(self.portal, [])
        addActionDropDownMenuIcons(self.portal, [])
        ai=self.portal.portal_actionicons
        icons = dict([
            ((x.getCategory(), x.getActionId()), x)
            for x in ai.listActionIcons()
        ])
        self.failIf(('object_buttons', 'cut') not in icons)
        self.failIf(('object_buttons', 'copy') not in icons)
        self.failIf(('object_buttons', 'paste') not in icons)
        self.failIf(('object_buttons', 'delete') not in icons)
        self.assertEqual(icons[('object_buttons', 'cut')].getExpression(), 'cut_icon.gif')
        self.assertEqual(icons[('object_buttons', 'copy')].getExpression(), 'copy_icon.gif')
        self.assertEqual(icons[('object_buttons', 'paste')].getExpression(), 'paste_icon.gif')
        self.assertEqual(icons[('object_buttons', 'delete')].getExpression(), 'delete_icon.gif')
        self.assertEqual(icons[('object_buttons', 'cut')].getTitle(), 'Cut')
        self.assertEqual(icons[('object_buttons', 'copy')].getTitle(), 'Copy')
        self.assertEqual(icons[('object_buttons', 'paste')].getTitle(), 'Paste')
        self.assertEqual(icons[('object_buttons', 'delete')].getTitle(), 'Delete')

    def testAddActionDropDownMenuIconsNoTool(self):
        # Should not break if actionicons tool is missing
        self.portal._delObject('portal_actionicons')
        addActionDropDownMenuIcons(self.portal, [])


class TestMigrations_v2_5(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.memberdata = self.portal.portal_memberdata
        self.catalog = self.portal.portal_catalog
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow

    def testInstallPlacefulWorkflow(self):
        if 'portal_placefulworkflow' in self.portal.objectIds():
            self.portal._delObject('portal_placeful_workflow')
        installPlacefulWorkflow(self.portal, [])
        self.failUnless('portal_placeful_workflow' in self.portal.objectIds())

    def testInstallPlacefulWorkflowTwice(self):
        if 'portal_placefulworkflow' in self.portal.objectIds():
            self.portal._delObject('portal_placeful_workflow')
        installPlacefulWorkflow(self.portal, [])
        installPlacefulWorkflow(self.portal, [])
        self.failUnless('portal_placeful_workflow' in self.portal.objectIds())

    def testInstallPortalSetup(self):
        if 'portal_setup' in self.portal.objectIds():
            self.portal._delObject('portal_setup')
        installPortalSetup(self.portal, [])
        self.failUnless('portal_setup' in self.portal.objectIds())

    def testInstallPortalSetupTwice(self):
        if 'portal_setup' in self.portal.objectIds():
            self.portal._delObject('portal_setup')
        installPortalSetup(self.portal, [])
        installPortalSetup(self.portal, [])
        self.failUnless('portal_setup' in self.portal.objectIds())

    def testInstallPlonePAS(self):
        qi = self.portal.portal_quickinstaller
        if qi.isProductInstalled('PlonePAS'):
            self.setRoles(('Manager',))
            qi.uninstallProducts(['PlonePAS'])
        self.failIf(qi.isProductInstalled('PlonePAS'))
        installPlonePAS(self.portal, [])
        self.failUnless(qi.isProductInstalled('PlonePAS'))

    def testInstallPlonePASTwice(self):
        qi = self.portal.portal_quickinstaller
        if qi.isProductInstalled('PlonePAS'):
            self.setRoles(('Manager',))
            qi.uninstallProducts(['PlonePAS'])
        installPlonePAS(self.portal, [])
        installPlonePAS(self.portal, [])
        self.failUnless(qi.isProductInstalled('PlonePAS'))

    def testInstallPlonePASWithEnvironmentVariableSet(self):
        qi = self.portal.portal_quickinstaller
        if qi.isProductInstalled('PlonePAS'):
            self.setRoles(('Manager',))
            qi.uninstallProducts(['PlonePAS'])
        self.failIf(qi.isProductInstalled('PlonePAS'))
        os.environ['SUPPRESS_PLONEPAS_INSTALLATION'] = 'YES'
        installPlonePAS(self.portal, [])
        self.failIf(qi.isProductInstalled('PlonePAS'))
        del os.environ['SUPPRESS_PLONEPAS_INSTALLATION']
        installPlonePAS(self.portal, [])
        self.failUnless(qi.isProductInstalled('PlonePAS'))

    def testInstallDeprecated(self):
        # Remove skin
        self.skins._delObject('plone_deprecated')
        skins = ['Plone Default', 'Plone Tableless']
        for s in skins:
            path = self.skins.getSkinPath(s)
            path = [p.strip() for p in  path.split(',')]
            path.remove('plone_deprecated')
            self.skins.addSkinSelection(s, ','.join(path))
        self.failIf('plone_deprecated' in
                           self.skins.getSkinPath('Plone Default').split(','))
        installDeprecated(self.portal, [])
        self.failUnless('plone_deprecated' in self.skins.objectIds())
        # it should be in the skin now
        self.assertEqual(self.skins.getSkinPath('Plone Default').split(',')[-3],
                         'plone_deprecated')
        self.assertEqual(self.skins.getSkinPath('Plone Tableless').split(',')[-3],
                         'plone_deprecated')

    def testInstallDeprecatedTwice(self):
        # Remove skin
        self.skins._delObject('plone_deprecated')
        skins = ['Plone Default', 'Plone Tableless']
        for s in skins:
            path = self.skins.getSkinPath(s)
            path = [p.strip() for p in  path.split(',')]
            path.remove('plone_deprecated')
            self.skins.addSkinSelection(s, ','.join(path))
        self.failIf('plone_deprecated' in
                           self.skins.getSkinPath('Plone Default').split(','))
        skin_len = len(self.skins.getSkinPath('Plone Default').split(','))
        installDeprecated(self.portal, [])
        installDeprecated(self.portal, [])
        self.failUnless('plone_deprecated' in self.skins.objectIds())
        # it should be in the skin now
        self.assertEqual(self.skins.getSkinPath('Plone Default').split(',')[-3],
                         'plone_deprecated')
        self.assertEqual(self.skins.getSkinPath('Plone Tableless').split(',')[-3],
                         'plone_deprecated')
        self.assertEqual(len(self.skins.getSkinPath('Plone Default').split(',')),
                         skin_len+1)

    def testInstallDeprecatedNoTool(self):
        # Remove skin
        self.portal._delObject('portal_skins')
        installDeprecated(self.portal, [])

    def testAddDragDropReorderJS(self):
        jsreg = self.portal.portal_javascripts
        script_ids = jsreg.getResourceIds()
        self.failUnless('dragdropreorder.js' in script_ids)
        # if dropdown.js is available dragdropreorder.js
        # should be positioned right underneath it
        if 'dropdown.js' in script_ids:
            posSE = jsreg.getResourcePosition('dragdropreorder.js')
            posHST = jsreg.getResourcePosition('dropdown.js')
            self.failUnless((posSE - 1) == posHST)

    def testAddGetEventTypeIndex(self):
        # Should add getEventType index
        self.catalog.delIndex('getEventType')
        addGetEventTypeIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('getEventType')
        self.assertEqual(index.__class__.__name__, 'KeywordIndex')

    def testAddGetEventTypeIndexTwice(self):
        # Should not fail if migrated again
        self.catalog.delIndex('getEventType')
        addGetEventTypeIndex(self.portal, [])
        addGetEventTypeIndex(self.portal, [])
        index = self.catalog._catalog.getIndex('getEventType')
        self.assertEqual(index.__class__.__name__, 'KeywordIndex')

    def testAddGetEventTypeIndexNoCatalog(self):
        # Should not fail if portal_catalog is missing
        self.portal._delObject('portal_catalog')
        addGetEventTypeIndex(self.portal, [])

    def testFixHomeAction(self):
        editActions = ('index_html',)
        for a in editActions:
            self.removeActionFromTool(a)
        fixHomeAction(self.portal, [])
        actions = [x.id for x in self.actions.listActions()]
        for a in editActions:
            self.failUnless(a in actions)

    def testFixHomeActionTwice(self):
        editActions = ('index_html',)
        for a in editActions:
            self.removeActionFromTool(a)
        fixHomeAction(self.portal, [])
        fixHomeAction(self.portal, [])
        actions = [x.id for x in self.actions.listActions()]
        for a in editActions:
            self.failUnless(a in actions)

    def testFixHomeActionNoTool(self):
        self.portal._delObject('portal_actions')
        fixHomeAction(self.portal, [])

    def testRemoveBogusSkin(self):
        # Add bogus skin
        self.skins.manage_skinLayers(add_skin=1, skinname='cmf_legacy',
                                  skinpath=['plone_forms','plone_templates'])
        self.failUnless(self.skins._getSelections().has_key('cmf_legacy'))
        removeBogusSkin(self.portal, [])
        # It should be gone
        self.failIf(self.skins._getSelections().has_key('cmf_legacy'))

    def testAddPloneSkinLayers(self):
        # Add bogus skin
        self.skins.manage_skinLayers(add_skin=1, skinname='foo_bar',
                                  skinpath=['plone_forms','plone_templates'])
        self.failUnless(self.skins._getSelections().has_key('foo_bar'))

        path = [p.strip() for p in self.skins.getSkinPath('foo_bar').split(',')]
        self.assertEqual(['plone_forms', 'plone_templates'], path)

        addPloneSkinLayers(self.portal, [])

        path = [p.strip() for p in self.skins.getSkinPath('foo_bar').split(',')]
        self.assertEqual(['plone_forms', 'plone_templates', 'plone_deprecated'], path)

    def testRemoveBogusSkinTwice(self):
        self.skins.manage_skinLayers(add_skin=1, skinname='cmf_legacy',
                                  skinpath=['plone_forms','plone_templates'])
        self.failUnless(self.skins._getSelections().has_key('cmf_legacy'))
        removeBogusSkin(self.portal, [])
        removeBogusSkin(self.portal, [])
        self.failIf(self.skins._getSelections().has_key('cmf_legacy'))

    def testRemoveBogusSkinNoSkin(self):
        self.failIf(self.skins._getSelections().has_key('cmf_legacy'))
        removeBogusSkin(self.portal, [])
        self.failIf(self.skins._getSelections().has_key('cmf_legacy'))

    def testRemoveBogusSkinNoTool(self):
        self.portal._delObject('portal_skins')
        removeBogusSkin(self.portal, [])

    def testSimplifyActions(self):
        # Should simplify a number of actions across multiple tools using the
        # view methods
        tool = self.portal.portal_actions
        paste = tool.object_buttons.paste
        rename = tool.object_buttons.rename
        contents = tool.object.folderContents
        index = tool.portal_tabs.index_html
        wkspace = tool.user.myworkspace
        # Set the expressions and conditions to their 2.5 analogues to test
        # every substitution
        paste._updateProperty('url_expr',
                'python:"%s/object_paste"%((object.isDefaultPageInFolder() or not object.is_folderish()) and object.getParentNode().absolute_url() or object_url)')
        rename._updateProperty('url_expr',
                'python:"%s/object_rename"%(object.isDefaultPageInFolder() and object.getParentNode().absolute_url() or object_url)')
        rename.edit('available_expr',
                'python:portal.portal_membership.checkPermission("Delete objects", object.aq_inner.getParentNode()) and portal.portal_membership.checkPermission("Copy or Move", object) and portal.portal_membership.checkPermission("Add portal content", object) and object is not portal and not (object.isDefaultPageInFolder() and object.getParentNode() is portal)')
        contents._updateProperty('url_expr',
                "python:((object.isDefaultPageInFolder() and object.getParentNode().absolute_url()) or folder_url)+'/folder_contents'")
        index._updateProperty('url_expr',
                'string: ${here/@@plone/navigationRootUrl}')
        wkspace._updateProperty('url_expr',
                                "python: portal.portal_membership.getHomeUrl()+'/workspace'")

        # Verify that the changes have been made
        paste = tool.object_buttons.paste
        self.failUnless("object.isDefaultPageInFolder()" in
                                                  paste.getProperty('url_expr'))
        # Run the action simplifications
        simplifyActions(self.portal, [])
        self.assertEqual(paste.getProperty('url_expr'),
                "string:${globals_view/getCurrentFolderUrl}/object_paste")
        self.assertEqual(rename.getProperty('url_expr'),
                "string:${globals_view/getCurrentObjectUrl}/object_rename")
        self.assertEqual(rename.getProperty('available_expr'),
                'python:checkPermission("Delete objects", globals_view.getParentObject()) and checkPermission("Copy or Move", object) and checkPermission("Add portal content", object) and not globals_view.isPortalOrPortalDefaultPage()')
        self.assertEqual(contents.getProperty('url_expr'),
                "string:${globals_view/getCurrentFolderUrl}/folder_contents")
        self.assertEqual(index.getProperty('url_expr'),
                "string:${globals_view/navigationRootUrl}")
        self.assertEqual(wkspace.getProperty('url_expr'),
                "string:${portal/portal_membership/getHomeUrl}/workspace")

    def testSimplifyActionsTwice(self):
        # Should result in the same string when applied twice
        tool = self.portal.portal_actions
        paste = tool.object_buttons.paste
        paste._updateProperty('url_expr',
                              'python:"%s/object_paste"%((object.isDefaultPageInFolder() or not object.is_folderish()) and object.getParentNode().absolute_url() or object_url)')

        # Verify that the changes have been made
        paste = tool.object_buttons.paste
        self.failUnless("object.isDefaultPageInFolder()" in
                                paste.getProperty('url_expr'))

        # Run the action simplifications twice
        simplifyActions(self.portal, [])
        simplifyActions(self.portal, [])

        # We should have the same result
        self.assertEqual(paste.getProperty('url_expr'),
                "string:${globals_view/getCurrentFolderUrl}/object_paste")

    def testSimplifyActionsNoTool(self):
        # Sholud not fail if the tool is missing
        self.portal._delObject('portal_actions')
        simplifyActions(self.portal, [])

    def testMigrateCSSRegExpression(self):
        # Should convert the expression using a deprecated script to use the
        # view
        css_reg = self.portal.portal_css
        resource = css_reg.getResource('RTL.css')
        resource.setExpression("python:object.isRightToLeft(domain='plone')")
        css_reg.cookResources()

        # Ensure the change worked
        resource = css_reg.getResource('RTL.css')
        self.failUnless('object.isRightToLeft' in resource.getExpression())

        # perform the migration
        migrateCSSRegExpression(self.portal, [])
        self.assertEqual(resource.getExpression(),
                "object/@@plone/isRightToLeft")

    def testMigrateCSSRegExpressionWith25Expression(self):
        # Should replace the restrictedTraverse call with the more compact
        # path expression
        css_reg = self.portal.portal_css
        resource = css_reg.getResource('RTL.css')
        resource.setExpression(
"python:object.restrictedTraverse('@@plone').isRightToLeft(domain='plone')")
        css_reg.cookResources()

        # perform the migration
        migrateCSSRegExpression(self.portal, [])
        self.assertEqual(resource.getExpression(),
                "object/@@plone/isRightToLeft")

    def testMigrateCSSRegExpressionTwice(self):
        # Should result in the same string when applied twice
        css_reg = self.portal.portal_css
        resource = css_reg.getResource('RTL.css')
        resource.setExpression("python:object.isRightToLeft(domain='plone')")
        css_reg.cookResources()

        # perform the migration twice
        migrateCSSRegExpression(self.portal, [])
        migrateCSSRegExpression(self.portal, [])
        self.assertEqual(resource.getExpression(),
                "object/@@plone/isRightToLeft")

    def testMigrateCSSRegExpressionNoTool(self):
        # Should not fail if the tool is missing
        self.portal._delObject('portal_css')
        migrateCSSRegExpression(self.portal, [])

    def testMigrateCSSRegExpressionNoResource(self):
        # Should not fail if the resource is missing
        css_reg = self.portal.portal_css
        css_reg.unregisterResource('RTL.css')
        migrateCSSRegExpression(self.portal, [])

class TestMigrations_v2_5_1(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.memberdata = self.portal.portal_memberdata
        self.catalog = self.portal.portal_catalog
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self.css = self.portal.portal_css

    def testRemovePloneCssFromRR(self):
        # Check to ensure that plone.css gets removed from portal_css
        self.css.registerStylesheet('plone.css', media='all')
        self.failUnless('plone.css' in self.css.getResourceIds())
        removePloneCssFromRR(self.portal, [])
        self.failIf('plone.css' in self.css.getResourceIds())

    def testRemovePloneCssFromRRTwice(self):
        # Should not fail if performed twice
        self.css.registerStylesheet('plone.css', media='all')
        self.failUnless('plone.css' in self.css.getResourceIds())
        removePloneCssFromRR(self.portal, [])
        removePloneCssFromRR(self.portal, [])
        self.failIf('plone.css' in self.css.getResourceIds())

    def testRemovePloneCssFromRRNoCSS(self):
        # Should not fail if the stylesheet is missing
        self.failIf('plone.css' in self.css.getResourceIds())
        removePloneCssFromRR(self.portal, [])

    def testRemovePloneCssFromRRNoTool(self):
        # Should not fail if the tool is missing
        self.portal._delObject('portal_css')
        removePloneCssFromRR(self.portal, [])

    def testAddEventRegistrationJS(self):
        jsreg = self.portal.portal_javascripts
        # unregister first
        jsreg.unregisterResource('event-registration.js')
        script_ids = jsreg.getResourceIds()
        self.failIf('event-registration.js' in script_ids)
        # migrate and test again
        addEventRegistrationJS(self.portal, [])
        script_ids = jsreg.getResourceIds()
        self.failUnless('event-registration.js' in script_ids)
        self.assertEqual(jsreg.getResourcePosition('event-registration.js'), 0)

    def testAddEventRegistrationJSTwice(self):
        # Should not break if migrated again
        jsreg = self.portal.portal_javascripts
        # unregister first
        jsreg.unregisterResource('event-registration.js')
        script_ids = jsreg.getResourceIds()
        self.failIf('event-registration.js' in script_ids)
        # migrate and test again
        addEventRegistrationJS(self.portal, [])
        addEventRegistrationJS(self.portal, [])
        script_ids = jsreg.getResourceIds()
        self.failUnless('event-registration.js' in script_ids)
        self.assertEqual(jsreg.getResourcePosition('event-registration.js'), 0)

    def testAddEventRegistrationJSNoTool(self):
        # Should not break if the tool is missing
        self.portal._delObject('portal_javascripts')
        addEventRegistrationJS(self.portal, [])

    def testFixupPloneLexicon(self):
        # Should update the plone_lexicon pipeline
        lexicon = self.portal.portal_catalog.plone_lexicon
        lexicon._pipeline = (object(), object())
        fixupPloneLexicon(self.portal, [])
        self.failUnless(isinstance(lexicon._pipeline[0], Splitter))
        self.failUnless(isinstance(lexicon._pipeline[1], CaseNormalizer))

    def testFixupPloneLexiconTwice(self):
        # Should not break if migrated again
        lexicon = self.portal.portal_catalog.plone_lexicon
        lexicon._pipeline = (object(), object())
        fixupPloneLexicon(self.portal, [])
        fixupPloneLexicon(self.portal, [])
        self.failUnless(isinstance(lexicon._pipeline[0], Splitter))
        self.failUnless(isinstance(lexicon._pipeline[1], CaseNormalizer))

    def testFixupPloneLexiconNoLexicon(self):
        # Should not break if plone_lexicon is missing
        self.portal.portal_catalog._delObject('plone_lexicon')
        fixupPloneLexicon(self.portal, [])

    def testFixupPloneLexiconNoTool(self):
        # Should not break if portal_catalog is missing
        self.portal._delObject('portal_catalog')
        fixupPloneLexicon(self.portal, [])

    def tesFixObjDeleteActionTwice(self):
        # Should not error if performed twice
        editActions = ('delete',)
        for a in editActions:
            self.removeActionFromTool(a)
        fixObjDeleteAction(self.portal, [])
        fixObjDeleteAction(self.portal, [])
        actions = [x.id for x in self.actions.listActions()
                   if x.id in editActions]
        # check that all of our deleted actions are now present
        for a in editActions:
            self.failUnless(a in actions)
        # ensure that they are present only once
        self.failUnlessEqual(len(editActions), len(actions))

    def testFixObjDeleteActionNoAction(self):
        # Should add the action
        editActions = ('delete',)
        for a in editActions:
            self.removeActionFromTool(a)
        fixObjDeleteAction(self.portal, [])
        actions = [x for x in self.actions.object_buttons.objectIds()
                   if x in editActions]
        for a in editActions:
            self.failUnless(a in actions)
        self.failUnlessEqual(len(editActions), len(actions))

    def testFixObjDeleteActionNoTool(self):
        self.portal._delObject('portal_actions')
        fixObjDeleteAction(self.portal, [])

    def testSetLoginFormInCookieAuth(self):
        setLoginFormInCookieAuth(self.portal, [])
        cookie_auth = self.portal.acl_users.credentials_cookie_auth
        self.failUnlessEqual(cookie_auth.getProperty('login_path'),
                             'require_login')

    def testSetLoginFormNoCookieAuth(self):
        # Shouldn't error
        uf = self.portal.acl_users
        uf._delOb('credentials_cookie_auth')
        setLoginFormInCookieAuth(self.portal, [])

    def testSetLoginFormAlreadyChanged(self):
        # Shouldn't change the value if it's not the default
        cookie_auth = self.portal.acl_users.credentials_cookie_auth
        cookie_auth.manage_changeProperties(login_path='foo')
        out = []
        setLoginFormInCookieAuth(self.portal, out)
        self.failIf(len(out) > 0)
        self.failIfEqual(cookie_auth.getProperty('login_path'),
                         'require_login')

class TestMigrations_v3_0(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.cp = getUtility(IControlPanel)
        self.icons = self.portal.portal_actionicons
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self.properties = self.portal.portal_properties
        self.cp = self.portal.portal_controlpanel

    def testEnableZope3Site(self):
        # First we remove the site and site manager
        disableSite(self.portal)
        clearSite(self.portal)
        self.portal.setSiteManager(None)

        # Then run the migration step
        enableZope3Site(self.portal, [])

        # And see if we have an ISite with a local site manager
        self.failUnless(ISite.providedBy(self.portal))
        gsm = getGlobalSiteManager()
        sm = getSiteManager(self.portal)
        self.failIf(gsm is sm)

    def testEnableZope3SiteTwice(self):
        # First we remove the site and site manager
        disableSite(self.portal)
        clearSite(self.portal)
        self.portal.setSiteManager(None)

        # Then run the migration step
        enableZope3Site(self.portal, [])
        enableZope3Site(self.portal, [])

        # And see if we have an ISite with a local site manager
        self.failUnless(ISite.providedBy(self.portal))
        gsm = getGlobalSiteManager()
        sm = getSiteManager(self.portal)
        self.failIf(gsm is sm)

    def testAddNewCSSFiles(self):
        cssreg = self.portal.portal_css
        added_ids = ['navtree.css', 'invisibles.css', 'forms.css']
        for id in added_ids:
            cssreg.unregisterResource(id)
        stylesheet_ids = cssreg.getResourceIds()
        for id in added_ids:
            self.failIf('navtree.css' in stylesheet_ids)
        addNewCSSFiles(self.portal, [])
        stylesheet_ids = cssreg.getResourceIds()
        for id in added_ids:
            self.failUnless(id in stylesheet_ids)
        # perform migration twice
        addNewCSSFiles(self.portal, [])
        for id in added_ids:
            self.failUnless(id in stylesheet_ids)

    def testAddDefaultAndForbiddenContentTypesProperties(self):
        # Should add the forbidden_contenttypes and default_contenttype property
        self.removeSiteProperty('forbidden_contenttypes')
        self.removeSiteProperty('default_contenttype')
        self.failIf(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
        self.failIf(self.properties.site_properties.hasProperty('default_contenttype'))
        addDefaultAndForbiddenContentTypesProperties(self.portal, [])
        self.failUnless(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
        self.failUnless(self.properties.site_properties.hasProperty('default_contenttype'))
        self.failUnless(self.properties.site_properties.forbidden_contenttypes == ( 
            'text/structured', 
            'text/x-rst', 
            'text/plain-pre', 
            'text/x-python', 
            'text/x-web-textile',
            )
        )

    def testAddDefaultAndForbiddenContentTypesPropertiesTwice(self):
        # Should not fail if migrated again
        self.removeSiteProperty('forbidden_contenttypes')
        self.removeSiteProperty('default_contenttype')
        self.failIf(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
        self.failIf(self.properties.site_properties.hasProperty('default_contenttype'))
        addDefaultAndForbiddenContentTypesProperties(self.portal, [])
        self.failUnless(self.properties.site_properties.forbidden_contenttypes == ( 
            'text/structured', 
            'text/x-rst', 
            'text/plain-pre', 
            'text/x-python', 
            'text/x-web-textile',
            )
        )
        self.properties.site_properties.forbidden_contenttypes = ('text/x-rst',)
        addDefaultAndForbiddenContentTypesProperties(self.portal, [])
        self.failUnless(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
        self.failUnless(self.properties.site_properties.hasProperty('default_contenttype'))
        # adding a second time should leave existing `forbidden_contenttypes` settings alone:
        self.failUnless(self.properties.site_properties.forbidden_contenttypes == ( 
            'text/x-rst', 
            )
        )
    def testAddTypesConfiglet(self):
        self.removeActionFromTool('TypesSettings', action_provider='portal_controlpanel')
        addTypesConfiglet(self.portal, [])
        self.failUnless('TypesSettings' in [action.getId() for action in self.cp.listActions()])
        types = self.cp.getActionObject('Plone/TypesSettings')
        self.assertEquals(types.action.text,
                          'string:${portal_url}/@@types-controlpanel.html')

    def testAddTypesConfigletTwice(self):
        self.removeActionFromTool('TypesSettings', action_provider='portal_controlpanel')
        addTypesConfiglet(self.portal, [])
        addTypesConfiglet(self.portal, [])
        self.failUnless('TypesSettings' in [action.getId() for action in self.cp.listActions()])
        types = self.cp.getActionObject('Plone/TypesSettings')
        self.assertEquals(types.action.text,
                          'string:${portal_url}/@@types-controlpanel.html')

    def testAddFormTabbingJS(self):
        jsreg = self.portal.portal_javascripts
        # unregister first
        jsreg.unregisterResource('form_tabbing.js')
        script_ids = jsreg.getResourceIds()
        self.failIf('form_tabbing.js' in script_ids)
        # migrate and test again
        addFormTabbingJS(self.portal, [])
        script_ids = jsreg.getResourceIds()
        self.failUnless('form_tabbing.js' in script_ids)
        # if collapsiblesections.js is available form_tabbing.js
        # should be positioned right underneath it
        if 'collapsiblesections.js' in script_ids:
            posSE = jsreg.getResourcePosition('form_tabbing.js')
            posHST = jsreg.getResourcePosition('collapsiblesections.js')
            self.failUnless((posSE - 1) == posHST)

    def testAddFormInputLabelJS(self):
        jsreg = self.portal.portal_javascripts
        # unregister first
        jsreg.unregisterResource('input-label.js')
        script_ids = jsreg.getResourceIds()
        self.failIf('input-label.js' in script_ids)
        # migrate and test again
        addFormInputLabelJS(self.portal, [])
        script_ids = jsreg.getResourceIds()
        self.failUnless('input-label.js' in script_ids)

    def testUpdateFTII18NDomain(self):
        doc = self.types.Document
        doc.i18n_domain = ''
        # Update FTI's
        updateFTII18NDomain(self.portal, [])
        # domain should have been updated
        self.assertEquals(doc.i18n_domain, 'plone')

    def testUpdateFTII18NDomainTwice(self):
        doc = self.types.Document
        doc.i18n_domain = ''
        # Update FTI's twice
        updateFTII18NDomain(self.portal, [])
        updateFTII18NDomain(self.portal, [])
        # domain should have been updated
        self.assertEquals(doc.i18n_domain, 'plone')

    def testLegacyPortletsConverted(self):
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)
        
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)
        
        for k in left:
            del left[k]
        for k in right:
            del right[k]
                
        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet']
        self.portal.right_slots = ['here/portlet_login/macros/portlet']
        
        convertLegacyPortlets(self.portal, [])
        
        self.assertEquals(self.portal.left_slots, [])
        self.assertEquals(self.portal.right_slots, [])
        
        lp = left.values()
        self.assertEquals(2, len(lp))
        self.assertEquals(lp[0].template, u'portlet_recent')
        self.assertEquals(lp[0].macro, u'portlet')
        
        self.failUnless(isinstance(lp[1], portlets.news.Assignment))
        
        rp = right.values()
        self.assertEquals(1, len(rp))
        self.failUnless(isinstance(rp[0], portlets.login.Assignment))
        
        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEquals(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))
        
    def testLegacyPortletsConvertedTwice(self):
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)
        
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)
        
        for k in left:
            del left[k]
        for k in right:
            del right[k]
            
        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet']
        self.portal.right_slots = ['here/portlet_login/macros/portlet']
        
        convertLegacyPortlets(self.portal, [])
        convertLegacyPortlets(self.portal, [])
        
        self.assertEquals(self.portal.left_slots, [])
        self.assertEquals(self.portal.right_slots, [])
        
        lp = left.values()
        self.assertEquals(2, len(lp))
        self.assertEquals(lp[0].template, u'portlet_recent')
        self.assertEquals(lp[0].macro, u'portlet')
        
        self.failUnless(isinstance(lp[1], portlets.news.Assignment))
        
        rp = right.values()
        self.assertEquals(1, len(rp))
        self.failUnless(isinstance(rp[0], portlets.login.Assignment))
        
        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEquals(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))
        
    def testLegacyPortletsConvertedNoSlots(self):
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)
        
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)
        
        for k in left:
            del left[k]
        for k in right:
            del right[k]
            
        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet']
        if hasattr(self.portal.aq_base, 'right_slots'):
            delattr(self.portal, 'right_slots')
        
        convertLegacyPortlets(self.portal, [])
        
        self.assertEquals(self.portal.left_slots, [])
        
        lp = left.values()
        self.assertEquals(2, len(lp))
        self.assertEquals(lp[0].template, u'portlet_recent')
        self.assertEquals(lp[0].macro, u'portlet')
        
        self.failUnless(isinstance(lp[1], portlets.news.Assignment))
        
        rp = right.values()
        self.assertEquals(0, len(rp))
        
        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEquals(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))
        
    def testLegacyPortletsConvertedBadSlots(self):
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)
        
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)
        
        for k in left:
            del left[k]
        for k in right:
            del right[k]
        
        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet',
                                  'foobar',]
        self.portal.right_slots = ['here/portlet_login/macros/portlet']
        
        convertLegacyPortlets(self.portal, [])
        
        self.assertEquals(self.portal.left_slots, [])
        self.assertEquals(self.portal.right_slots, [])
        
        lp = left.values()
        self.assertEquals(2, len(lp))
        self.assertEquals(lp[0].template, u'portlet_recent')
        self.assertEquals(lp[0].macro, u'portlet')
        
        self.failUnless(isinstance(lp[1], portlets.news.Assignment))
        
        rp = right.values()
        self.assertEquals(1, len(rp))
        self.failUnless(isinstance(rp[0], portlets.login.Assignment))
        
        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEquals(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))
        
    def testLegacyPortletsConvertedNoMembersFolder(self):
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)
        
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)
        
        for k in left:
            del left[k]
        for k in right:
            del right[k]
        
        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet',
                                  'foobar',]
        self.portal.right_slots = ['here/portlet_login/macros/portlet']
        
        
        self.portal._delObject('Members')
        
        convertLegacyPortlets(self.portal, [])
        
        self.assertEquals(self.portal.left_slots, [])
        self.assertEquals(self.portal.right_slots, [])
        
        lp = left.values()
        self.assertEquals(2, len(lp))
        self.assertEquals(lp[0].template, u'portlet_recent')
        self.assertEquals(lp[0].macro, u'portlet')
        
        self.failUnless(isinstance(lp[1], portlets.news.Assignment))
        
        rp = right.values()
        self.assertEquals(1, len(rp))
        self.failUnless(isinstance(rp[0], portlets.login.Assignment))

    def testAddIconForCalendarSettingsConfiglet(self):
        # Should add the calendar action icon
        self.removeActionIconFromTool('CalendarSettings')
        addIconForCalendarSettingsConfiglet(self.portal, [])
        self.failUnless('CalendarSettings' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddIconForCalendarSettingsConfigletTwice(self):
        # Should not fail if migrated again
        self.removeActionIconFromTool('CalendarSettings')
        addIconForCalendarSettingsConfiglet(self.portal, [])
        addIconForCalendarSettingsConfiglet(self.portal, [])
        self.failUnless('CalendarSettings' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddIconForCalendarSettingsConfigletNoTool(self):
        # Should not fail if portal_actionicons is missing
        self.portal._delObject('portal_actionicons')
        addIconForCalendarSettingsConfiglet(self.portal, [])

    def testAddCalendarConfiglet(self):
        self.removeActionFromTool('CalendarSettings', action_provider='portal_controlpanel')
        addCalendarConfiglet(self.portal, [])
        self.failUnless('CalendarSettings' in [x.getId() for x in self.cp.listActions()])
    
    def testAddCalendarConfigletTwice(self):
        # Should not fail if done twice
        self.removeActionFromTool('CalendarSettings', action_provider='portal_controlpanel')
        addCalendarConfiglet(self.portal, [])
        addCalendarConfiglet(self.portal, [])
        self.failUnless('CalendarSettings' in [x.getId() for x in self.cp.listActions()])
    
    def testAddCalendarConfigletNoTool(self):
        # Should not fail if tool is missing
        self.portal._delObject('portal_controlpanel')
        addCalendarConfiglet(self.portal, [])

    def testUpdateSearchAndMailHostConfiglet(self):
        search = self.cp.getActionObject('Plone/SearchSettings')
        mail = self.cp.getActionObject('Plone/MailHost')
        search.action = Expression('string:search')
        mail.action = Expression('string:mail')
        updateSearchAndMailHostConfiglet(self.portal, [])
        self.assertEquals(search.action.text,
                          'string:${portal_url}/@@search-controlpanel.html')
        self.assertEquals(mail.action.text,
                          'string:${portal_url}/@@mail-controlpanel.html')
    
    def testUpdateSearchAndMailHostConfigletTwice(self):
        # Should not fail if done twice
        search = self.cp.getActionObject('Plone/SearchSettings')
        mail = self.cp.getActionObject('Plone/MailHost')
        search.action = Expression('string:search')
        mail.action = Expression('string:mail')
        updateSearchAndMailHostConfiglet(self.portal, [])
        updateSearchAndMailHostConfiglet(self.portal, [])
        self.assertEquals(search.action.text,
                          'string:${portal_url}/@@search-controlpanel.html')
        self.assertEquals(mail.action.text,
                          'string:${portal_url}/@@mail-controlpanel.html')
    
    def testUpdateSearchAndMailHostConfigletNoTool(self):
        # Should not fail if tool is missing
        self.portal._delObject('portal_controlpanel')
        updateSearchAndMailHostConfiglet(self.portal, [])

    def testRegisterToolsAsUtilities(self):
        sm = getSiteManager(self.portal)
        interfaces = (IControlPanel, IInterfaceTool, IMigrationTool,
                      ITranslationServiceTool, )
        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal, [])
        for i in interfaces:
            self.failIf(sm.queryUtility(i) is None)

    def testRegisterToolsAsUtilitiesTwice(self):
        # Should not fail if done twice
        sm = getSiteManager(self.portal)
        interfaces = (IControlPanel, IInterfaceTool, IMigrationTool,
                      ITranslationServiceTool, )
        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal, [])
        registerToolsAsUtilities(self.portal, [])
        for i in interfaces:
            self.failIf(sm.queryUtility(i) is None)
    
    def testInstallKss(self, unregister=True):
        'Test kss migration'
        jstool = self.portal.portal_javascripts
        csstool = self.portal.portal_css
        mt = self.portal.mimetypes_registry
        mtid = 'text/kss'
        st = self.portal.portal_skins
        skins = ['Plone Default', 'Plone Tableless']
        if unregister:
            # unregister first
            for id, _compression, _enabled in installKss.js_all:
                jstool.unregisterResource(id)
            for id in installKss.css_all + installKss.kss_all:
                csstool.unregisterResource(id)
            mt.manage_delObjects((mtid, ))
            js_ids = jstool.getResourceIds()
            for id, _compression, _enabled in installKss.js_all:
                self.failIf(id in js_ids)
            css_ids = csstool.getResourceIds()
            for id in installKss.css_all + installKss.kss_all:
                self.failIf(id in css_ids)
            self.failIf(mtid in mt.list_mimetypes())
            selections = st._getSelections()
            for s in skins:
                if not selections.has_key(s):
                    continue
                path = st.getSkinPath(s)
                path = [p.strip() for p in  path.split(',')]
                path_changed = False
                if 'plone.kss' in path:
                    path.remove('plone.kss')
                    path_changed = True
                if 'at.kss' in path:
                    path.remove('at.kss')
                    path_changed = True
                if path_changed:
                    st.addSkinSelection(s, ','.join(path))
            # XXX we cannot remove the directory views, so...
        # migrate and test again
        installKss(self.portal, [])
        js_ids = jstool.getResourceIds()
        css_dict = csstool.getResourcesDict()
        for id in installKss.js_unregister:
            self.failIf(id in js_ids)
        for id, _compression, _enabled in installKss.js_all:
            self.assert_(id in js_ids, '%r is not registered' % id)
        for id in installKss.css_all:
            self.assert_(id in css_dict)
        for id in installKss.kss_all:
            self.assert_(id in css_dict)
            value = css_dict[id]
            self.assertEqual(value.getEnabled(), True)
            self.assertEqual(value.getRel(), 'k-stylesheet')
            self.assertEqual(value.getRendering(), 'link')
        self.assert_(mtid in mt.list_mimetypes())
        # check the skins
        selections = st._getSelections()
        for s in skins:
            if not selections.has_key(s):
               continue
            path = st.getSkinPath(s)
            path = [p.strip() for p in  path.split(',')]
            self.assert_('plone_kss' in path)
            self.assert_('archetypes_kss' in path)
        self.assert_(hasattr(aq_base(st), 'plone_kss'))
        self.assert_(hasattr(aq_base(st), 'archetypes_kss'))

    def testInstallKssTwice(self):
        'Test kss migration, twice'
        self.testInstallKss()
        self.testInstallKss(unregister=False)
        
    def testInstallRedirectorUtility(self):
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IRedirectionStorage)
        installRedirectorUtility(self.portal, [])
        self.failIf(sm.queryUtility(IRedirectionStorage) is None)

    def testInstallRedirectorUtilityTwice(self):
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IRedirectionStorage)
        installRedirectorUtility(self.portal, [])
        installRedirectorUtility(self.portal, [])
        self.failIf(sm.queryUtility(IRedirectionStorage) is None)
        
    def testAddContentRulesAction(self):
        self.portal.portal_actions.object_buttons._delObject('contentrules')
        addContentRulesAction(self.portal, [])
        self.failUnless('contentrules' in self.portal.portal_actions.object_buttons.objectIds())
        
    def testAddContentRulesActionTwice(self):
        self.portal.portal_actions.object_buttons._delOb('contentrules')
        addContentRulesAction(self.portal, [])
        addContentRulesAction(self.portal, [])
        self.failUnless('contentrules' in self.portal.portal_actions.object_buttons.objectIds())
        
    def testAddContentRulesActionNoTool(self):
        self.portal._delOb('portal_actions')
        addContentRulesAction(self.portal, [])
        
    def testAddContentRulesActionNoCategory(self):
        self.portal.portal_actions._delOb('object_buttons')
        addContentRulesAction(self.portal, [])
        
    def testAddReaderEditorRoles(self):
        self.portal._delRoles(['Reader', 'Editor'])
        addReaderAndEditorRoles(self.portal, [])
        self.failUnless('Reader' in self.portal.valid_roles())
        self.failUnless('Editor' in self.portal.valid_roles())
        self.failUnless('Reader' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('Editor' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('View' in [r['name'] for r in self.portal.permissionsOfRole('Reader') if r['selected']])
        self.failUnless('Modify portal content' in [r['name'] for r in self.portal.permissionsOfRole('Editor') if r['selected']])
        
    def testAddReaderEditorRolesPermissionOnly(self):
        self.portal.manage_permission('View', [], True)
        self.portal.manage_permission('Modify portal content', [], True)
        addReaderAndEditorRoles(self.portal, [])
        self.failUnless('Reader' in self.portal.valid_roles())
        self.failUnless('Editor' in self.portal.valid_roles())
        self.failUnless('Reader' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('Editor' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('View' in [r['name'] for r in self.portal.permissionsOfRole('Reader') if r['selected']])
        self.failUnless('Modify portal content' in [r['name'] for r in self.portal.permissionsOfRole('Editor') if r['selected']])
        
    def testAddReaderEditorRolesTwice(self):
        self.portal._delRoles(['Reader', 'Editor'])
        addReaderAndEditorRoles(self.portal, [])
        addReaderAndEditorRoles(self.portal, [])
        self.failUnless('Reader' in self.portal.valid_roles())
        self.failUnless('Editor' in self.portal.valid_roles())
        self.failUnless('Reader' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('Editor' in self.portal.acl_users.portal_role_manager.listRoleIds())
        self.failUnless('View' in [r['name'] for r in self.portal.permissionsOfRole('Reader') if r['selected']])
        self.failUnless('Modify portal content' in [r['name'] for r in self.portal.permissionsOfRole('Editor') if r['selected']])

    def testMigrateLocalroleForm(self):
        fti = self.portal.portal_types['Document']
        aliases = fti.getMethodAliases()
        aliases['sharing'] = 'folder_localrole_form'
        fti.setMethodAliases(aliases)
        fti.addAction('test', 'Test', 'string:${object_url}/folder_localrole_form', None, 'View', 'object_tabs')
        migrateLocalroleForm(self.portal, [])
        self.assertEquals('@@sharing', fti.getMethodAliases()['sharing'])
        test_action = fti.listActions()[-1]
        self.assertEquals('string:${object_url}/@@sharing', test_action.getActionExpression())

    def testMigrateLocalroleFormTwice(self):
        fti = self.portal.portal_types['Document']
        aliases = fti.getMethodAliases()
        aliases['sharing'] = 'folder_localrole_form'
        fti.setMethodAliases(aliases)
        fti.addAction('test', 'Test', 'string:${object_url}/folder_localrole_form', None, 'View', 'object_tabs')
        migrateLocalroleForm(self.portal, [])
        migrateLocalroleForm(self.portal, [])
        self.assertEquals('@@sharing', fti.getMethodAliases()['sharing'])
        test_action = fti.listActions()[-1]
        self.assertEquals('string:${object_url}/@@sharing', test_action.getActionExpression())
        
    def testMigrateLocalroleFormNoTool(self):
        self.portal._delObject('portal_types')
        migrateLocalroleForm(self.portal, [])

    def testReorderUserActions(self):
        self.actions.user.moveObjectsToTop(['logout', 'undo', 'join'])
        reorderUserActions(self.portal, [])
        # build a dict that has the position as the value to make it easier to
        # compare postions in the ordered list of actions
        n = 0
        sort = {}
        for action in self.actions.user.objectIds():
            sort[action] = n
            n += 1
        self.failUnless(sort['mystuff'] < sort['preferences'])
        self.failUnless(sort['preferences'] < sort['undo'])
        self.failUnless(sort['undo'] < sort['logout'])
        self.failUnless(sort['login'] < sort['join'])

    def testReorderUserActionsTwice(self):
        self.actions.user.moveObjectsToTop(['logout', 'undo', 'join'])
        reorderUserActions(self.portal, [])
        reorderUserActions(self.portal, [])
        # build a dict that has the position as the value to make it easier to
        # compare postions in the ordered list of actions
        n = 0
        sort = {}
        for action in self.actions.user.objectIds():
            sort[action] = n
            n += 1
        self.failUnless(sort['mystuff'] < sort['preferences'])
        self.failUnless(sort['preferences'] < sort['undo'])
        self.failUnless(sort['undo'] < sort['logout'])
        self.failUnless(sort['login'] < sort['join'])

    def testReorderUserActionsNoTool(self):
        self.portal._delObject('portal_actions')
        reorderUserActions(self.portal, [])

    def testReorderUserActionsIncompleteActions(self):
        self.actions.user.moveObjectsToTop(['logout', 'undo', 'join'])
        self.actions.user._delObject('preferences')
        reorderUserActions(self.portal, [])
        # build a dict that has the position as the value to make it easier to
        # compare postions in the ordered list of actions
        n = 0
        sort = {}
        for action in self.actions.user.objectIds():
            sort[action] = n
            n += 1
        self.failUnless(sort['mystuff'] < sort['undo'])
        self.failUnless(sort['undo'] < sort['logout'])
        self.failUnless(sort['login'] < sort['join'])

    def testUpdateRtlCSSexpression(self):
        cssreg = self.portal.portal_css
        rtl = cssreg.getResource('RTL.css')
        rtl.setExpression('string:foo')
        updateRtlCSSexpression(self.portal, [])
        expr = rtl.getExpression()
        self.failUnless(expr == "python:portal.restrictedTraverse('@@plone_portal_state').is_rtl()")

    def testUpdateRtlCSSexpressionTwice(self):
        # perform migration twice
        cssreg = self.portal.portal_css
        rtl = cssreg.getResource('RTL.css')
        rtl.setExpression('string:foo')
        updateRtlCSSexpression(self.portal, [])
        updateRtlCSSexpression(self.portal, [])
        expr = rtl.getExpression()
        self.failUnless(expr == "python:portal.restrictedTraverse('@@plone_portal_state').is_rtl()")

    def testAddMaintenanceConfiglet(self):
        self.removeActionFromTool('Maintenance', action_provider='portal_controlpanel')
        addMaintenanceConfiglet(self.portal, [])
        self.failUnless('Maintenance' in [x.getId() for x in self.cp.listActions()])

    def testAddMaintenanceConfigletTwice(self):
        self.removeActionFromTool('Maintenance', action_provider='portal_controlpanel')
        addMaintenanceConfiglet(self.portal, [])
        addMaintenanceConfiglet(self.portal, [])
        self.failUnless('Maintenance' in [x.getId() for x in self.cp.listActions()])

    def testAddIconForMaintenanceConfiglet(self):
        # Should add the maintenance action icon
        self.removeActionIconFromTool('Maintenance')
        addIconForCalendarSettingsConfiglet(self.portal, [])
        self.failUnless('Maintenance' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddIconForMaintenanceConfigletTwice(self):
        # Should add the maintenance action icon
        self.removeActionIconFromTool('Maintenance')
        addIconForCalendarSettingsConfiglet(self.portal, [])
        addIconForCalendarSettingsConfiglet(self.portal, [])
        self.failUnless('Maintenance' in [x.getActionId() for x in self.icons.listActionIcons()])

    def testAddMaintenanceProperty(self):
        # adds a site property to portal_properties
        self.removeSiteProperty('number_of_days_to_keep')
        addMaintenanceProperty(self.portal, [])
        tool = self.portal.portal_properties
        sheet = tool.site_properties
        self.failUnless(sheet.hasProperty('number_of_days_to_keep'))
    
    def testAddTableContents(self):
        css = self.portal.portal_css
        js = self.portal.portal_javascripts
        css.manage_removeStylesheet("toc.css")
        js.manage_removeScript("toc.js")
        addTableContents(self.portal, [])
        self.failUnless("toc.js" in js.getResourceIds())
        self.failUnless("toc.css" in css.getResourceIds())
        addTableContents(self.portal, [])
        self.failUnless("toc.js" in js.getResourceIds())
        self.failUnless("toc.css" in css.getResourceIds())
        
    def testUpdateMemberSecurity(self):
        pprop = getToolByName(self.portal, 'portal_properties')
        self.assertEquals(
                pprop.site_properties.getProperty('allowAnonymousViewAbout'),
                False)

        pmembership = getToolByName(self.portal, 'portal_membership')
        self.assertEquals(pmembership.memberareaCreationFlag, False)

        self.assertEquals(self.portal.getProperty('validate_email'), True)

        app_roles = self.portal.rolesOfPermission(permission='Add portal member')
        app_perms = self.portal.permission_settings(permission='Add portal member')
        acquire_check = app_perms[0]['acquire']
        reg_roles = []
        for appperm in app_roles:
            if appperm['selected'] == 'SELECTED':
                reg_roles.append(appperm['name'])
        self.failUnless('Manager' in reg_roles)
        self.failUnless('Owner' in reg_roles)
        self.failUnless(acquire_check == '')


    def testPloneS5(self):
        pa = self.portal.portal_actions
        self.removeActionIconFromTool('s5_presentation')
        self.removeActionFromTool('s5_presentation', action_provider='portal_actions')
        installS5(self.portal, [])
        self.failUnless('s5_presentation' in [x.getActionId() for x in self.icons.listActionIcons()])
        self.failUnless('s5_presentation' in [x.getId() for x in pa.listActions()])
        installS5(self.portal, [])
        self.failUnless('s5_presentation' in [x.getActionId() for x in self.icons.listActionIcons()])
        self.failUnless('s5_presentation' in [x.getId() for x in pa.listActions()])


class TestMigrations_v3_0_Actions(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        
        # Create dummy old ActionInformation
        self.reply = ActionInformation('reply',
            title='Reply',
            category='reply_actions',
            condition='context/replyAllowed',
            permissions=(AccessInactivePortalContent, ),
            priority=10,
            visible=True,
            action='context/reply'
        )
        self.discussion = self.portal.portal_discussion
        self.discussion._actions = (self.reply, )

    def testMigrateActions(self):
        self.failUnless(self.discussion._actions == (self.reply, ))
        
        migrateOldActions(self.portal, [])

        reply_actions = getattr(self.actions, 'reply_actions', None)
        self.failIf(reply_actions is None)
        reply = getattr(reply_actions, 'reply', None)
        self.failIf(reply is None)
        self.failUnless(isinstance(reply, Action))

        # Verify all data has been migrated correctly to the new Action
        data = reply.getInfoData()[0]
        self.assertEquals(data['category'], 'reply_actions')
        self.assertEquals(data['title'], 'Reply')
        self.assertEquals(data['visible'], True)
        self.assertEquals(data['permissions'], (AccessInactivePortalContent, ))
        self.assertEquals(data['available'].text, 'context/replyAllowed')
        self.assertEquals(data['url'].text, 'context/reply')

        # Make sure the original action has been removed
        self.failUnless(len(self.discussion._actions) == 0)

    def testMigrateActionsTwice(self):
        self.failUnless(self.discussion._actions == (self.reply, ))

        migrateOldActions(self.portal, [])
        migrateOldActions(self.portal, [])

        reply_actions = getattr(self.actions, 'reply_actions', None)
        self.failIf(reply_actions is None)
        reply = getattr(reply_actions, 'reply', None)
        self.failIf(reply is None)
        self.failUnless(isinstance(reply, Action))

        # Verify all data has been migrated correctly to the new Action
        data = reply.getInfoData()[0]
        self.assertEquals(data['category'], 'reply_actions')
        self.assertEquals(data['title'], 'Reply')
        self.assertEquals(data['visible'], True)
        self.assertEquals(data['permissions'], (AccessInactivePortalContent, ))
        self.assertEquals(data['available'].text, 'context/replyAllowed')
        self.assertEquals(data['url'].text, 'context/reply')

        # Make sure the original action has been removed
        self.failUnless(len(self.discussion._actions) == 0)

    def testUpdateActionsI18NDomain(self):
        migrateOldActions(self.portal, [])
        reply = self.actions.reply_actions.reply
        self.assertEquals(reply.i18n_domain, '')        

        updateActionsI18NDomain(self.portal, [])
        
        self.assertEquals(reply.i18n_domain, 'plone')

    def testUpdateActionsI18NDomainTwice(self):
        migrateOldActions(self.portal, [])
        reply = self.actions.reply_actions.reply
        self.assertEquals(reply.i18n_domain, '')        

        updateActionsI18NDomain(self.portal, [])
        updateActionsI18NDomain(self.portal, [])

        self.assertEquals(reply.i18n_domain, 'plone')

    def beforeTearDown(self):
        if len(self.discussion._actions) > 0:
            self.discussion._actions = ()

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v2_1_1))
    suite.addTest(makeSuite(TestMigrations_v2_1_2))
    suite.addTest(makeSuite(TestMigrations_v2_1_3))
    suite.addTest(makeSuite(TestMigrations_v2_5))
    suite.addTest(makeSuite(TestMigrations_v2_5_1))
    suite.addTest(makeSuite(TestMigrations_v3_0))
    suite.addTest(makeSuite(TestMigrations_v3_0_Actions))
    return suite

if __name__ == '__main__':
    framework()
