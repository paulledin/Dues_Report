 # -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 13:40:15 2024

@author: Paul Ledin
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import locale

st.set_page_config(
    page_title="America's Credit Unions",
    layout="wide",
    initial_sidebar_state="expanded")

locale.setlocale(locale.LC_ALL, 'C')

thePassPhrase = st.secrets["thePassPhrase"]
dbConn = st.connection("snowflake")
###############################################################################
#Function Definitions
###############################################################################
@st.cache_data
def getCUData(nimble_cuna_id):
    df_cuData = dbConn.session().sql("SELECT f1.nimble_cuna_id, f1.name, f1.st_address, f1.st_city, f1.st_state, f1.st_zip_code, f1.members, f1.total_assets, f1.league_name, f1.afl, f1.status, f1.nafcu_affiliated, f1.league_affiliated, f1.survivor_id, f2.league_name_nimble, merger_date FROM acus_data.core_data.core_data f1 LEFT JOIN acus_data.core_data.league_codes f2 ON f1.league_code=f2.league_code WHERE f1.nimble_cuna_id='" + nimble_cuna_id + "' ").to_pandas()
    df_cuData.loc[df_cuData['LEAGUE_NAME'].isna(), 'LEAGUE_NAME'] = df_cuData['LEAGUE_NAME_NIMBLE']
    return (df_cuData)

@st.cache_data
def getStateNames():
    return (dbConn.session().sql("SELECT full_name FROM acus_data.core_data.state_codes ").to_pandas())

@st.cache_data
def getLeagueNames():
    df_league_name = dbConn.session().sql("SELECT distinct(league_name) FROM acus_data.core_data.core_data WHERE league_name IS NOT NULL AND league_name!='Alternatives FCU' AND status='A' ORDER BY league_name ").to_pandas()
    df_league_name = pd.concat([pd.DataFrame({"LEAGUE_NAME": ['']}), df_league_name])
    return (df_league_name)

@st.cache_data
def getCUDuesPremlimEst(nimble_cuna_id):
    return (dbConn.session().sql("SELECT status, afl, league_affiliated, nafcu_affiliated, current_members, current_assets, june_assets, num_mergers, cuna_dues_2025, nafcu_dues_2025, full_amt_2025, expected_dues, formula FROM acus_data.dues.dues_est_2025 WHERE nimble_cuna_id='" + nimble_cuna_id + "' ").to_pandas())

@st.cache_data
def getCUDuesPremlimEstByLeague(league_name):
    return (dbConn.session().sql("SELECT f1.nimble_cuna_id, f2.name AS \"CU Name\", f2.status AS \"Status\", f1.current_members AS \"March Members\", f1.current_assets AS \"March Assets\", f1.june_assets AS \"June Assets\", f1.full_amt_2025 AS \"ACUs Full Amount\", f2.afl, f2.league_affiliated FROM acus_data.dues.dues_est_2025 f1 LEFT JOIN acus_data.core_data.core_data f2 ON f1.nimble_cuna_id=f2.nimble_cuna_id WHERE f1.league_name='" + league_name + "' ").to_pandas())

@st.cache_data
def getMergers(survivor_id):
    return (dbConn.session().sql("SELECT nimble_cuna_id, name AS \"Name\", st_state AS \"State\", merger_date AS \"Merger_Date\" FROM acus_data.core_data.core_data WHERE merger_date>='2023-03-31' AND merger_date<='2024-03-31' AND survivor_id='" + survivor_id + "' ").to_pandas())

@st.cache_data
def getPreviousDues(year):
    return (dbConn.session().sql("SELECT nimble_cuna_id, full_amt_" + year + "_with5pct_cap AS \"Dues_" + year + "\" FROM acus_data.dues.CUNA_DUES_" + year).to_pandas())

@st.cache_data
def getMembersAndAssets(period):
    return (dbConn.session().sql("SELECT nimble_cuna_id, members, total_assets FROM acus_data.ncua_data.cuFinancials_" + period).to_pandas())

@st.cache_data
def getQtrAdjustements(year, quarter, nimble_cuna_id):
    return (dbConn.session().sql("SELECT nimble_cuna_id, name AS \"Name\", status AS \"Status\", afl AS \"AFL\", league_affiliated AS \"LG AFL\", full_amt_2025 AS \"Dues 2025\", expected_2025 AS \"Expected\", collected_2025 AS \"Collected\", reafl_100pct AS \"Re-AFL 100%\", reafl_partial AS \"Re-AFL Partial\", disafl AS \"Dis-AFL\", hardship AS \"Hardship\", other AS \"Other\", dead AS \"Dead\", merged AS \"Mergers\", comments AS \"Comments\", direct_pay AS \"Direct Pay\" FROM acus_data.dues.dues_est_" + year + "_Q" + quarter +  " WHERE nimble_cuna_id='" + nimble_cuna_id + "' ").to_pandas())

def expandFlagDescriptions(df):
    df.loc[df['STATUS'] == 'A', 'STATUS'] = 'Active'
    df.loc[df['STATUS'] == 'P', 'STATUS'] = 'Pending'
    df.loc[df['STATUS'] == 'L', 'STATUS'] = 'Liquidated'
    df.loc[df['STATUS'] == 'M', 'STATUS'] = 'Merged'
    df.loc[df['STATUS'] == 'I', 'STATUS'] = 'Inactive'

    df.loc[df['AFL'] == 'A', 'AFL'] = 'Yes'
    df.loc[df['AFL'] == 'N', 'AFL'] = 'No'

    df.loc[df['NAFCU_AFFILIATED'] == 'A', 'NAFCU_AFFILIATED'] = 'Yes'
    df.loc[df['NAFCU_AFFILIATED'] == 'N', 'NAFCU_AFFILIATED'] = 'No'

    df.loc[df['LEAGUE_AFFILIATED'] == 'A', 'LEAGUE_AFFILIATED'] = 'Yes'
    df.loc[df['LEAGUE_AFFILIATED'] == 'N', 'LEAGUE_AFFILIATED'] = 'No'
    return (df)

###############################################################################
#Start building Streamlit App
###############################################################################
with st.sidebar:
    st.markdown('![alt text](https://raw.githubusercontent.com/paulledin/data/master/ACUS.jpg)')
    passphrase = st.text_input("### Please enter the passphrase:")

if (passphrase != thePassPhrase):
    if len(passphrase) > 0:
        st.markdown('# Passphrase not correct....')
        st.markdown('### Please try again or contact: pledin@americascreditunions.org for assistance.')
else:
    with st.sidebar:
        st.title('Dues Report')
    
        report_type = ['Individual CU','State', 'League']
        selected_report_type = st.selectbox('Report Type:', report_type)

        if (selected_report_type == 'State'):
            selected_state = st.selectbox('State:', getStateNames())
        elif (selected_report_type == 'League'):
            selected_league = st.selectbox('League:', getLeagueNames())
        else:
            nimble_cuna_id = st.text_input("NIMBLE_CUNA_ID:", "10013583")  
                
    col = st.columns((9, 1), gap='medium')
    with col[0]:
        if (selected_report_type == 'Individual CU'):
            thisCU = expandFlagDescriptions(getCUData(nimble_cuna_id))
            prelimDues = expandFlagDescriptions(getCUDuesPremlimEst(nimble_cuna_id))
            mergers = getMergers(nimble_cuna_id)
            cunaDues2024 = getPreviousDues('2024')
            thisCU = thisCU.merge(cunaDues2024, how='left', on='NIMBLE_CUNA_ID')

            cunaDues2023 = getPreviousDues('2023')
            march_2023_cuFins = getMembersAndAssets('202303')
            mergers = mergers.merge(march_2023_cuFins, how='left', on='NIMBLE_CUNA_ID')
            mergers = mergers.merge(cunaDues2023, how='left', on='NIMBLE_CUNA_ID')
            mergers["Dues_2024"] = (mergers["MEMBERS"] * 0.12) + (mergers["TOTAL_ASSETS"] * 0.000018)
            mergers.loc[mergers['TOTAL_ASSETS'] < 5000000, 'Dues_2024'] = mergers["Dues_2024"] / 2
            mergers["prev_year_diff"] = (mergers["Dues_2024"] - mergers["Dues_2023"]) / mergers["Dues_2023"]   
            mergers.loc[mergers['prev_year_diff'] > 0.05, 'Dues_2024'] = mergers["Dues_2023"] * 1.05
            mergers["Dues_2024"] = round(mergers["Dues_2024"], 0)
            mergers.drop(['prev_year_diff', 'MEMBERS', 'TOTAL_ASSETS', 'Dues_2023'], axis=1, inplace = True)
 
            st.markdown('#### 2025 Dues Calculation for - ' + thisCU['NAME'].loc[thisCU.index[0]])
            
            if(len(thisCU) == 0):
                st.markdown('#### !! No Credit Unions Found Matching NIMBLE_CUNA_ID -> ' + nimble_cuna_id + ' !!')
            else:
                st.markdown('---')
                st.markdown('#### Credit Union')
                st.markdown('**NIMBLE_CUNA_ID:** ' + thisCU['NIMBLE_CUNA_ID'].loc[thisCU.index[0]])
                st.markdown('**Name:** ' + thisCU['NAME'].loc[thisCU.index[0]])
                st.markdown('**Physical Address:** ' + thisCU['ST_ADDRESS'].loc[thisCU.index[0]] + ', ' + thisCU['ST_CITY'].loc[thisCU.index[0]] + ' ' + thisCU['ST_STATE'].loc[thisCU.index[0]] + ', ' + thisCU['ST_ZIP_CODE'].loc[thisCU.index[0]])
                
                current_members = "**Current Members:**  {members:,.0f} "
                st.markdown(current_members.format(members = thisCU['MEMBERS'].loc[thisCU.index[0]]))
                current_assets = "**Current Assets:**  ${assets:,.0f} "
                st.markdown(current_assets.format(assets = thisCU['TOTAL_ASSETS'].loc[thisCU.index[0]]))
                st.markdown('**Current Status:** ' + thisCU['STATUS'].loc[thisCU.index[0]])

                st.markdown('**League:** ' + str(thisCU['LEAGUE_NAME'].loc[thisCU.index[0]]))
                st.markdown('---')
                
                st.markdown('#### Preliminary Estimate')

                if (len(prelimDues) == 0):
                    st.write('No preliminary dues were calculated for this credit union because they merged/liquidated and/or didn\'t file a March NCUA Call Report.')
                else:
                    st.markdown('**Status:** ' + prelimDues['STATUS'].loc[thisCU.index[0]])
                    st.markdown('**Legacy CUNA Affiliated:** ' + prelimDues['AFL'].loc[thisCU.index[0]])
                    st.markdown('**Legacy NAFCU Affiliated:** ' + prelimDues['NAFCU_AFFILIATED'].loc[thisCU.index[0]])
                    st.markdown('**League Affiliated:** ' + prelimDues['LEAGUE_AFFILIATED'].loc[thisCU.index[0]])

                    current_members = "**March 2024 Members:**  {members:,.0f} "
                    st.markdown(current_members.format(members = prelimDues['CURRENT_MEMBERS'].loc[prelimDues.index[0]]))
                    current_assets = "**March 2024 Assets:**  ${assets:,.0f} "
                    st.markdown(current_assets.format(assets = prelimDues['CURRENT_ASSETS'].loc[prelimDues.index[0]]))
                    june_assets = "**June 2024 Assets:**  ${assets:,.0f} "
                    st.markdown(june_assets.format(assets = prelimDues['JUNE_ASSETS'].loc[prelimDues.index[0]]))
                
                    cuna_dues = "**2025 Legacy CUNA Dues Est:**  ${dues:,.0f} "
                    st.markdown(cuna_dues.format(dues = prelimDues['CUNA_DUES_2025'].loc[prelimDues.index[0]]))
                    nafcu_dues = "**2025 Legacy NAFCU Dues Est:**  ${dues:,.0f} "
                    st.markdown(nafcu_dues.format(dues = prelimDues['NAFCU_DUES_2025'].loc[prelimDues.index[0]]))

                    st.markdown('**Formula Used:** ' + prelimDues['FORMULA'].loc[thisCU.index[0]])
                
                    full_amt = "**2025 Full Amount Due:**  ${dues:,.0f} "
                    st.markdown(full_amt.format(dues = prelimDues['FULL_AMT_2025'].loc[prelimDues.index[0]]))

                    expected = "**2025 Expected Dues:**  ${dues:,.0f} "
                    st.markdown(expected.format(dues = prelimDues['FULL_AMT_2025'].loc[prelimDues.index[0]]))

                    num_mergers = "**Mar 2023 - Mar 2024 Mergers:**  {mergers:,.0f} "
                    st.markdown(num_mergers.format(mergers = prelimDues['NUM_MERGERS'].loc[prelimDues.index[0]]))

                    st.markdown("**Merger Detail:**")
                    st.write(mergers)

                    st.markdown("**Legacy CUNA Calculation:**")

                    dues_calc = round(prelimDues['CURRENT_ASSETS'].loc[prelimDues.index[0]] * 0.000018 + prelimDues['CURRENT_MEMBERS'].loc[prelimDues.index[0]] * 0.12, 0)

                    if(dues_calc > 322131):
                        dues_calc = 322131

                    dues_by_formula = "Est Dues based on forumula =  ${dues:,.0f} "
                    st.markdown(dues_by_formula.format(dues = dues_calc))
                    cuna_cap_calc = "- ({members:,.0f} * 0.12) + (${assets:,.0f} * 0.000018) "
                    st.markdown(cuna_cap_calc.format(members = prelimDues['CURRENT_MEMBERS'].loc[prelimDues.index[0]], assets = prelimDues['CURRENT_ASSETS'].loc[prelimDues.index[0]]))

                    previous_yr_dues = "Previous Years Dues =  ${prev_dues:,.0f} "
                    st.markdown(previous_yr_dues.format(prev_dues = thisCU['Dues_2024'].loc[thisCU.index[0]]))
             
                    mergee_dues = "- Previous Years Dues from Mergers = ${mergee_dues:,.0f} "
                    st.markdown(mergee_dues.format(mergee_dues = sum(mergers['Dues_2024'])))

                    total_dues = "- Previous Years Dues Incl. Mergers = ${total_dues:,.0f} "
                    st.markdown(total_dues.format(total_dues = sum(mergers['Dues_2024']) + sum(thisCU['Dues_2024'])))

                    plus_5_pct = "- Previous Years Dues Incl. Mergers x 1.05 = ${plus_5_pct:,.0f} "
                    st.markdown(plus_5_pct.format(plus_5_pct = (sum(mergers['Dues_2024']) + sum(thisCU['Dues_2024']))*1.05))

                    if (dues_calc == 322131):
                        st.write("**=> Credit Union is at the Dues Cap of $322,131.**")
                    elif ((sum(mergers['Dues_2024']) + sum(thisCU['Dues_2024']))*1.05 <= dues_calc):   
                        st.write("**=> Formula Calculated Amount is >= 105% of Last Year's Full Amount.**")
                        full_amt = "**=> Legacy CUNA 2025 Full Amount:**  ${dues:,.0f} "
                        st.markdown(full_amt.format(dues = prelimDues['FULL_AMT_2025'].loc[prelimDues.index[0]]))
                    else:
                        st.write("**=> Formula Calculated Amount is <= 105% of Last Year's Full Amount.**")
                        full_amt = "**=> 2025 Legacy CUNA Full Amount:**  ${dues:,.0f} "
                        st.markdown(full_amt.format(dues = prelimDues['FULL_AMT_2025'].loc[prelimDues.index[0]]))

                    st.markdown('---')
                st.markdown('#### Q1 - Adjustments')

                q1_adjs = getQtrAdjustements('2025', '1', nimble_cuna_id)
                st.markdown("**1st Quarter Adjustment Detail:**")
                if (len(q1_adjs) == 0):
                    if (thisCU['STATUS'].loc[thisCU.index[0]] == 'Merged'):
                        survivor_cu = getCUData(thisCU['SURVIVOR_ID'].loc[thisCU.index[0]])
                        comments = 'Merged with ' + survivor_cu['NAME'].loc[survivor_cu.index[0]] + ' (' + thisCU['SURVIVOR_ID'].loc[thisCU.index[0]] + ') on ' + thisCU['MERGER_DATE'].loc[thisCU.index[0]]
                    q1_adjs = pd.DataFrame({"NIMBLE_CUNA_ID": [nimble_cuna_id], "Name": thisCU['NAME'].loc[thisCU.index[0]], "Status": thisCU['STATUS'].loc[thisCU.index[0]], "Comments": [comments]})
                st.write(q1_adjs)

                st.markdown('---')
        elif (selected_report_type == 'State'):
            st.markdown("**State Reports Coming Soon!!!**")
        else:
            thisLgCUs = getCUDuesPremlimEstByLeague(selected_league)
            st.write(len(thisLgCUs))

            st.write(thisLgCUs)

            st.markdown('### 2025 Dues Calculation for - ' + selected_league)
            st.markdown('---')

            st.markdown('#### Credit Unions with Dual Membership')
            df_dual_affiliates = thisLgCUs.loc[(thisLgCUs['AFL'] == 'A') & (thisLgCUs['LEAGUE_AFFILIATED'] == 'A')]
            st.write(df_dual_affiliates)
            st.write(len(df_dual_affiliates))
            st.markdown('---')

            st.markdown('#### Affiliated With America\'s Credit Unions Only/Paid To League:')
            st.markdown('---')

            st.markdown('#### Collected By America\'s Credit Unions:')
            st.markdown('---')

            st.markdown('#### Affiliated With League Only:')
            st.markdown('---')

            st.markdown('#### Not Affiliated With Both America\'s Credit Unions and League:')
            st.markdown('---')




    with col[1]:
        st.markdown('')
        




