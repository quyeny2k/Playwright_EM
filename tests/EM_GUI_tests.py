import pytest
from playwright.sync_api import Page, expect
import time

from tests.conftest import LOGINRETRIES, transformpos2canvas, EMHOST, transformpos2canvasincommissiondialog, handle_dialog

@pytest.mark.skip
@pytest.mark.parametrize("username, password", (["admin", "Pass"],
                                             ["user", "pass"]))
def test_login_bad_password(page, username, password):
    page.goto(EMHOST)
    expect(page).to_have_title("Enlighted Manage")

    page.locator("#userNameTextBox").fill(username)
    page.locator("#passwordTextBox").fill(password)
    page.get_by_role("button", name="Sign in").click()
    print(page.locator("#error").text_content())
    expect(page.locator("#error")).to_contain_text(
        "Username and/or password are invalid. Please try again.")


@pytest.mark.skip
@pytest.mark.parametrize("username, password", (["admin", "Pass"],
                                             ["admin", "pass"]))
def test_bad_login_attempt_warning(page: Page, username, password):
    global LOGINRETRIES
    print(LOGINRETRIES)
    page.goto(EMHOST)
    expect(page).to_have_title("Enlighted Manage")

    page.locator("#userNameTextBox").fill(username)
    page.locator("#passwordTextBox").fill(password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.locator("#error")).to_contain_text(fr"attempt(s) remaining")
    LOGINRETRIES -= 1


def test_EM_LicenseSupport_page(login):
    page = login
    print("Test EM License Support page")
    expect(page).to_have_url(f"{EMHOST}/ems/licenseSupport/management.ems")
    uuidtext = page.locator('#pricingDiv').inner_text()
    assert len(uuidtext.split(' : ')[1]) != 0
    expect(page.locator('#areacount')).to_contain_text("Area Count : 20")
    expect(page.locator('#sensorlicenseusage')).to_contain_text("Sensor License Usage* : 10 of 0")


def test_EM_OrgNavigation(emfacilitiespage):
    print("Test EM Organization navigation")
    page = emfacilitiespage
    time.sleep(2)

    page.get_by_role("tab", name="Facilities").get_by_role("link").click()
    expect(page.locator("#company_1")).to_contain_text("The Home Depot")
    page.locator("#campus_1").get_by_role("insertion").first.click()
    expect(page.locator("#campus_1")).to_contain_text("Setup 2 #395")
    page.get_by_role("insertion").nth(2).click()
    expect(page.locator("#building_1")).to_contain_text("Setup 2 #395_1")
    if page.locator('#building_1').evaluate('el => el.classList.contains("jstree-closed")'):
        page.locator("#building_1").get_by_role("insertion").first.click()
    floorloc = page.locator('[rel="floor"]')
    assert floorloc.count() == 2
    expect(floorloc.first).to_contain_text("5i_floor", timeout=1, use_inner_text=True)
    expect(floorloc.nth(1)).to_contain_text("Main", timeout=1, use_inner_text=True)
    expect(page.get_by_role("link", name="5i_floor")).to_be_visible()
    expect(page.get_by_role("link", name="Main")).to_be_visible()
    page.get_by_role("link", name="Main").click()

    #time.sleep(5)  # Wait for the load(s) javascript to load the iframe completely
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("link", name="Energy Consumption")).to_be_visible()
    time.sleep(5)

@pytest.mark.skip
def test_EM_Devices_tab(emfacilitiespage):
    print("Test EM Devices Tab")
    page = emfacilitiespage
    #page.wait_for_load_state("networkidle")
    time.sleep(2)

    expect(page.get_by_role("link", name="Devices")).to_be_visible()
    page.get_by_role("link", name="Devices").click()

    devicestabframe = page.locator('#installFrame')
    tabs = devicestabframe.content_frame.locator("#innerdevicecenter").locator('[role="tab"]')
    tablabels = ["Gateways", "Sensors", "Plugloads", "Switch", "Others", "Scene Templates"]

    expect(tabs).to_have_count(len(tablabels))
    for i in range(len(tablabels)):
        expect(tabs.nth(i)).to_contain_text(tablabels[i])


    # Check Gateways tab details
    tabs.nth(0).get_by_role("link", name="Gateways").wait_for(state="visible")
    tabs.nth(0).get_by_role("link", name="Gateways").click()
    gatewaysframe = devicestabframe.content_frame.locator("#gatewaysFrame")
    gatewaysframe.content_frame.locator("#gatewayTable").wait_for(state='visible')
    gatewaytable = gatewaysframe.content_frame.locator("#gatewayTable")
    gatewayrows = gatewaytable.locator('[role="row"]')
    # First row contains column labels.  Ignore
    # 2nd row and beyond contains GW info.  Each row contains 11 "gridcell" attributes.
    # 1. Checkbox
    # 2. Gateway ID (hidden)
    # 3. Gatway name
    # 4. Channel
    # 5. PanID
    # 6. Version
    # 7. Commissioned (True/False) (hidden)
    # 8. No. of devices associated with this gateway
    # 9. No. of ERCs associated with this gateway
    # 10. State (Commissioned, Pending, Discovered)

    gateways = [["280", "GWaaaaaf", "15", "AAAF", "3.6.0 b7", "true", "8", "2", "COMMISSIONED"],
                ["793", "GW404faf", "15", "4FAF", "103.7.0 b1", "true", "6", "2", "COMMISSIONED"]]
    for i in range(gatewayrows.count() - 1):
        gwinfo = gatewayrows.nth(i+1).locator('[role="gridcell"]')
        for j in range(1, 10):
            expect(gwinfo.nth(j)).to_contain_text(gateways[i][j-1], timeout=1)
            if j == 10:
                expect(gwinfo.nth(j).get_by_role("button")).to_have_count(2)
                expect(gwinfo.nth(j).get_by_role("button").nth(0)).to_contain_text("Edit")
                expect(gwinfo.nth(j).get_by_role("button").nth(0)).to_contain_text("Delete")


    # Check Sensors tab details
    tabs.nth(1).get_by_role("link", name="Sensors").click()
    fixturesframe = devicestabframe.content_frame.locator("#fixturesFrame")
    fixturesframe.content_frame.locator("#fixtureTable").wait_for(state='visible')
    fixturestable = fixturesframe.content_frame.locator("#fixtureTable")
    fixturerows = fixturestable.locator('[role="row"]')

    suinfo = None
    sensors = {"Sensor010001": ["825", "1", " ", "", "01:00:01", "Sensor010001", "Unknown", "SU-5E-01", "5.16.3 b123", "GWaaaaaf", "Default", "", "Commission"],
               "Sensor000001": ["824", "1", " ", "", "00:00:01", "Sensor000001", "Unknown", "SU-5E-01", "5.16.3 b123", "GWaaaaaf", "Default", "", "Commission"],
               "Sensorde4212": ["14", "9", "7", "/ems/themes/default/images/floorplan64/connectivityProblem.png", "de:42:12", "Sensorde4212", "LED Box Light", "SU-5S-HRW", "5.18.4 b0", "GW404faf", "Open Office_Default", "", "Edit"],
               "Sensor2345a2": ["217", "10", "7", "/ems/themes/default/images/floorplan64/connectivityHealthy.png", "23:45:a2", "Sensor2345a2", "LED Box Light", "SU-5E-01", "5.18.4 b0", "GW404faf", "Private Office_Default", "", "Edit"],
               "Sensor171a32": ["200", "10", "6", "/ems/themes/default/images/floorplan64/connectivityHealthy.png", "17:1a:32", "Sensor171a32", "TW_CCT_Analog", "SU-5E-01", "5.17.3 b0", "GW404faf", "Private Office_Default", "", "Edit"]
               }
    for i in [1, 2, 3, 9, 10]:  # Corresponding to sensor rows in Sensors tab
        suinfo = fixturerows.nth(i).locator('[role="gridcell"]')
        targetsu = sensors[suinfo.nth(6).inner_text()]
        for j in range(1, 14):
            if j == 4:
                continue
                # if suinfo.nth(j).locator("img").count() == 0:
                #     expect(suinfo.nth(j)).to_contain_text(targetsu[j-1], timeout=1)
                # else:
                #     expect(suinfo.nth(j).locator("img")).to_have_attribute("src", targetsu[j-1], timeout=1)
            elif j == 12:
                continue
            else:
                expect(suinfo.nth(j)).to_contain_text(targetsu[j-1], timeout=1)

    # Check fixture details
    suinfo.nth(13).get_by_role("button", name="Edit").click()
    page.locator('[role="dialog"]').nth(1).wait_for(state="visible")
    expect(page.locator('[role="dialog"]').nth(1)).to_be_visible()
    fixturedetailsdialog = page.locator('[role="dialog"]')
    fixturedetailscontent = fixturedetailsdialog.nth(1).locator('#fixture-form')
    fixturedetails = fixturedetailscontent.locator('[class="fieldWrapper"]')
    # Check fixture name
    expect(fixturedetails.nth(0).locator('[class="fieldValue"]>input')).to_have_value(targetsu[5])
    # Check location
    expect(fixturedetails.nth(1).locator('[class="fieldValue"]')).to_contain_text("Setup 2 #395->Setup 2 #395_1->Main", use_inner_text=True)
    # Check fixture ID
    expect(fixturedetails.nth(2).locator('[class="fieldValue"]')).to_contain_text(targetsu[0], use_inner_text=True)
    # Check Model No.
    expect(fixturedetails.nth(5).locator('[class="fieldValue"]')).to_contain_text(targetsu[7], use_inner_text=True)
    # Check GW name
    expect(fixturedetails.nth(6).locator('[class="fieldValue"]')).to_contain_text(targetsu[9], use_inner_text=True)
    #

    # Print fixture details
    for i in range(49):
        if i in [0, 4]:
            print(i, fixturedetails.nth(i).locator('[class="fieldLabel"]').inner_text(),
                  fixturedetails.nth(0).locator('[class="fieldValue"]>input').input_value())
        elif i in [15, 34]:
            print(i, fixturedetails.nth(i).locator('[class="fieldLabel"]').inner_text(), fixturedetails.nth(i).locator('[class="fieldValue"]>select').get_by_role("option", selected=True).inner_text())
        elif i in [21, 16, 17, 27, 42]:
            continue
        elif i > 44:
            print(i, fixturedetails.nth(i).inner_text(), fixturedetails.nth(i).get_by_role("checkbox").is_checked())
        else:
            print(i, fixturedetails.nth(i).locator('[class="fieldLabel"]').inner_text(),
                  fixturedetails.nth(i).locator('[class="fieldValue"]').inner_text())

    fixturedetailsdialog.get_by_role("button", name="Close").click()

@pytest.mark.skip
def test_EM_Floor_Plan_tab(emfacilitiespage):
    page = emfacilitiespage
    time.sleep(2)

    sulocations = {
        "Sensordddd01": {"x": 858, "y": 2843},
        "Sensordddd02": {"x": 1201, "y": 2861},
        "Sensorde4212": {"x": 635, "y": 1430},
        "Sensor171a32": {"x": 3134, "y": 610},
        "Sensor2345a2": {"x": 906, "y": 1411}
    }

    gwlocations = {
        "GW404faf": {"x": 707, "y": 1549},
        "GWe429c0": {"x": 2000, "y": 2000}
    }

    # Interact with floor plan
    expect(page.get_by_role("link", name="Floor Plan")).to_be_visible()
    page.get_by_role("link", name="Floor Plan").click()
    devicestatuspopup = page.locator('#popup')

    expect(page.locator('#tab_fp')).to_be_visible()

    canvas = page.locator("canvas")
    canvasdims = canvas.bounding_box()
    scalefactor = max (5000 / canvasdims["width"], 3500 / canvasdims["height"])
    # Check gateways status
    # Right click GWe429c0
    dev = "GWe429c0"
    canvas.click(position=transformpos2canvas(gwlocations[dev], scalefactor))

    expect(devicestatuspopup).to_be_visible()
    expect(devicestatuspopup).to_contain_text(f"{dev}Bound Fixtures: 0")
    assert "ol-popup-content" not in dict(devicestatuspopup.evaluate('el => el.classList')).values()  # Popup backgroup should be non-colored
    time.sleep(5)
    assert "ol-popup-content-success" in dict(
        devicestatuspopup.evaluate('el => el.classList')).values()  # Popup backgroup should be non-colored

    # Check sensor status
    # Right click Sensordddd01
    dev = "Sensordddd01"
    canvas.click(button="right", position=transformpos2canvas(sulocations[dev], scalefactor))
    expect(page.get_by_text("Assign ProfileAssign Fixture")).to_be_visible()
    expect(page.get_by_text("Assign ProfileAssign Fixture").locator('[role="menuitem"]')).to_have_count(12)

    menuitems = page.get_by_text("Assign ProfileAssign Fixture").locator('[role="menuitem"]')
    for i in range(12):
        print(menuitems.nth(i).inner_text())
    #time.sleep(3)
    # Close the popup
    page.locator('[role="presentation"]').nth(13).click(position={"x": 100, "y": 100}, timeout=1000)
    #time.sleep(1)
    # Select Sensordddd02 to verify the popup
    dev = "Sensordddd02"
    page.locator("canvas").click(position={"x": 100, "y":100})  # Unselect the device
    time.sleep(1)
    page.locator("canvas").click(position=transformpos2canvas(sulocations[dev], scalefactor))

    # Check if the device connection popup appears
    # Device connection popup only appears if the last connection exceeds the threshold
    # Otherwise, the device details popup shall appear
    # Check device with connection error (last connection exceeds threshold)

    expect(devicestatuspopup).to_be_visible()
    expect(devicestatuspopup).to_contain_text(f"{dev}Last Connected2024-07-23 09:46:52")

    # Check when hovering above device icon, device details popup appears for 5 seconds then go back to device connection details popup
    page.locator("canvas").hover(position=transformpos2canvas(sulocations[dev], scalefactor), timeout=10000)
    time.sleep(5)
    expect(devicestatuspopup).to_contain_text(f"{dev}  -  Open Office_Default - Auto37% ON32.00 WNormalOccupied1 min, 35 sec agoNormal70.8 F")

    # Check device connection details popup reappears
    time.sleep(5)
    expect(devicestatuspopup).to_contain_text(f"{dev}Last Connected2024-07-23 09:46:52")
    page.locator("canvas").click(position={"x": 100, "y": 100})  # Unselect the device
    time.sleep(1)
    # Check device with good connection
    dev = "Sensor171a32"
    page.locator("canvas").hover(position=transformpos2canvas(sulocations[dev], scalefactor), timeout=5000)
    expect(devicestatuspopup).to_contain_text(f"{dev}  -  Private Office_Default - Auto")
    classes = dict(devicestatuspopup.evaluate('el => el.classList'))
    assert "ol-popup-content" not in classes.values()  # Popup backgroup is not non-colored

    page.locator("canvas").click(position={"x": 100, "y": 100})  # Unselect the device
    time.sleep(1)
    dev = "Sensor2345a2"
    page.locator("canvas").hover(position=transformpos2canvas(sulocations[dev], scalefactor), timeout=10000)
    expect(devicestatuspopup).to_contain_text(f"{dev}  -  Private Office_Default - Auto")
    classes = dict(devicestatuspopup.evaluate('el => el.classList'))
    assert 'ol-popup-content-success' not in classes.values()
    time.sleep(5)
    classes = dict(devicestatuspopup.evaluate('el => el.classList'))
    assert 'ol-popup-content-success' in classes.values()

@pytest.mark.skip
def test_EM_Gateway_Delete_Failed_w_fixtures(emfacilitiespage):
    print("Test EM Gateway Delete failure with associated fixtures")
    page = emfacilitiespage
    #page.wait_for_load_state("networkidle")
    time.sleep(2)

    expect(page.get_by_role("link", name="Devices")).to_be_visible()
    page.get_by_role("link", name="Devices").click()
    page.wait_for_load_state("networkidle")
    devicestabframe = page.locator('#installFrame')
    gatewaysframe = devicestabframe.content_frame.locator("#gatewaysFrame")
    gatewaysframe.click()
    gatewaysframe.wait_for(timeout=5000, state="visible")
    gatewaytable = gatewaysframe.content_frame.locator("#gatewayTable")
    gatewayrows = gatewaytable.locator('[role="row"]')
    for i in range(1, gatewayrows.count()):
        if "GWaaaaaf" in gatewayrows.nth(i).inner_text():
            def handle_gw_delete_dialog(dialog):
                assert (dialog.type == 'alert'
                        and dialog.message == "This Gateway has fixture(s) associated with it.  It cannot be deleted")
                dialog.accept()

            page.on('dialog', handle_gw_delete_dialog)

            gatewayrows.nth(i).get_by_role("button", name="Delete").click()
            break
    #expect(gatewayrows.nth(1)).to_contain_text("GWaaaaaf")

@pytest.mark.skip
def test_EM_Gateway_Delete_Cancel(emfacilitiespage):
    print("Test EM Gateway Delete failure with associated fixtures")
    page = emfacilitiespage
    #page.wait_for_load_state("networkidle")
    time.sleep(2)

    expect(page.get_by_role("link", name="Devices")).to_be_visible()
    page.get_by_role("link", name="Devices").click()
    page.wait_for_load_state("networkidle")
    devicestabframe = page.locator('#installFrame')
    gatewaysframe = devicestabframe.content_frame.locator("#gatewaysFrame")
    gatewaysframe.click()
    gatewaysframe.wait_for(timeout=5000, state="visible")
    gatewaytable = gatewaysframe.content_frame.locator("#gatewayTable")
    gatewayrows = gatewaytable.locator('[role="row"]')
    for i in range(1, gatewayrows.count()):
        if "GWe429c0" in gatewayrows.nth(i).inner_text():
            def handle_gw_delete_dialog(dialog):
                assert (dialog.type == 'alert'
                        and dialog.message == "This Gateway has fixture(s) associated with it.  It cannot be deleted")
                dialog.dismiss()

            page.on('dialog', handle_gw_delete_dialog)

            gatewayrows.nth(i).get_by_role("button", name="Delete").click()
            page.wait_for_load_state("networkidle")
            expect(gatewayrows.nth(i)).to_contain_text("GWe429c0")
            break

@pytest.mark.skip
def test_EM_Gateway_Commission(emfacilitiespage):
    print("Test EM Gateway Commission")
    page = emfacilitiespage
    #page.wait_for_load_state("networkidle")
    time.sleep(2)

    expect(page.get_by_role("link", name="Devices")).to_be_visible()
    page.get_by_role("link", name="Devices").click()
    page.wait_for_load_state("networkidle")

    devicestabframe = page.locator('#installFrame')
    gatewaysframe = devicestabframe.content_frame.locator("#gatewaysFrame")
    gatewaysframe.click()
    gatewaysframe.wait_for(timeout=5000, state="visible")

    # Discover uncommissioned gateways
    gatewaysframe.content_frame.locator('#discoverGatewayBtn').click()
    # page.wait_for_load_state("networkidle")
    time.sleep(1)
    gatewaysframe.content_frame.locator("#gatewayTable").wait_for(state='visible')
    gatewaytable = gatewaysframe.content_frame.locator("#gatewayTable")
    gatewayrows = gatewaytable.locator('[role="row"]')

    uncommissionedgws = dict()
    # Get all uncommissioned gateways
    for i in range(1, gatewayrows.count()):
        if "DISCOVERED" in gatewayrows.nth(i).inner_text():
            columns = gatewayrows.nth(i).locator('[role="gridcell"]')
            # uncommissionedgws has key = gwid and value = {"row": row# in the gatewaytable, "name": gateway name}
            uncommissionedgws[columns.nth(1).inner_text()] = {"row": i, "name": columns.nth(2).inner_text()}

    # Not using the uncommissioendgws dictionary for now.  Just perform bulk commission all gws
    gatewaysframe.content_frame.get_by_role('button', name="Commission").first.click()
    # The first item returned is the bulk commission button and the rest are Commission button for each gateway

    #page.wait_for_load_state("domcontentloaded")
    time.sleep(3)
    # Get all gateways id
    commdialogbox = page.locator('#commissionDialogBox')
    gwids = commdialogbox.locator('#uncommissionedGateways').evaluate("el => Array.from(el.options).map(opt => opt.value)")

    # Make sure that all uncommissioned gws are listed in the uncommissionedGateways pane
    assert sorted(gwids) == sorted(list(uncommissionedgws.keys()))

    # Use the first gw from the uncommissionedgws dictionary
    gwid = list(uncommissionedgws.keys())[0]
    commdialogbox.locator('#uncommissionedGateways').select_option(gwid)
    time.sleep(1)
    gwdetailspane = commdialogbox.locator('#gwDetails')
    gwdetailspane.locator('#channel').select_option('10')
    time.sleep(5)
    #Radio network ID is prepopulated so no need to change anything to this field
    #gwdetailspane.locator('#wirelessNetworkId').fill("29c0")

    # Use default encryption type - AES128 and security key so no need to interact with these fields

    # Get canvas
    canvas = page.locator('canvas')
    canvasdimensions = canvas.bounding_box()
    scalefactor = max( 5000 / canvasdimensions["width"], 3500 / canvasdimensions["height"])
    print("Scale factor = %.2f" % scalefactor)
    print("Canvas position: %s" % transformpos2canvasincommissiondialog({"x": 2000, "y": 2000}, scalefactor))
    canvas.click(position=transformpos2canvasincommissiondialog({"x": 2000, "y": 2000}, scalefactor), button="right")
    expect(page.get_by_text("Commission and Place")).to_be_visible()
    page.get_by_text("Commission and Place").click()
    page.wait_for_load_state("networkidle")

    # Check if gw commission succeeds
    expect(page.locator('#gc_message_Div')).to_contain_text("Success")
    # Make sure that GW is removed from the Uncommissioned pane
    assert gwid not in commdialogbox.locator('#uncommissionedGateways').evaluate("el => Array.from(el.options).map(opt => opt.value)")
    page.locator('#gwc-done-btn').click()
    page.wait_for_load_state()
    expect(canvas).not_to_be_visible()

    # Check if GW status is updated accordingly
    gatewayrows = gatewaytable.locator('[role="row"]')
    for i in range(1, gatewayrows.count()):
        if uncommissionedgws[gwid]["name"] in gatewayrows.nth(i).inner_text():
            columns = gatewayrows.nth(i).locator('[role="gridcell"]')
            expect(columns.nth(3)).to_contain_text('10')
            expect(columns.nth(4)).to_contain_text('29C0')
            expect(columns.nth(9)).to_contain_text('COMMISSIONED')
            expect(columns.nth(10).get_by_role("button")).to_have_count(2)
            expect(columns.nth(10).get_by_role("button").nth(0)).to_contain_text("Edit")
            expect(columns.nth(10).get_by_role("button").nth(1)).to_contain_text("Delete")