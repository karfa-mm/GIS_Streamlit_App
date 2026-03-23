import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
import os
import zipfile
import tempfile

# إعداد الصفحة
st.set_page_config(layout="wide", page_title="GIS Joint Tool")

st.title("🌐 تطبيق الربط المكاني والوصفي (GIS)")
st.markdown("---")

# وظيفة قراءة الملفات الجغرافية
def load_gis_data(file):
    if file is not None:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                if file.name.endswith('.zip'):
                    with zipfile.ZipFile(file, 'r') as z:
                        z.extractall(tmpdir)
                    for r, d, files in os.walk(tmpdir):
                        for f in files:
                            if f.endswith('.shp'):
                                return gpd.read_file(os.path.join(r, f))
                elif file.name.endswith('.geojson'):
                    return gpd.read_file(file)
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")
    return None

# --- القسم الأول: رفع الملفات ---
col1, col2 = st.columns(2)

with col1:
    st.header("1️⃣ الملف الأساسي (Left)")
    file1 = st.file_uploader("ارفع (Shapefile ZIP) أو (GeoJSON)", key="L")
    gdf1 = load_gis_data(file1)
    if gdf1 is not None:
        st.write("أول 5 صفوف:")
        st.dataframe(gdf1.head(5))
        # عرض الخريطة
        m1 = leafmap.Map(draw_control=False, measure_control=False)
        m1.add_gdf(gdf1, layer_name="Base")
        m1.to_streamlit(height=300)

with col2:
    st.header("2️⃣ الملف الثانوي (Right)")
    file2 = st.file_uploader("ارفع (Shapefile ZIP) أو (GeoJSON)", key="R")
    gdf2 = load_gis_data(file2)
    if gdf2 is not None:
        st.write("أول 5 صفوف:")
        st.dataframe(gdf2.head(5))
        # عرض الخريطة
        m2 = leafmap.Map(draw_control=False, measure_control=False)
        m2.add_gdf(gdf2, layer_name="Join")
        m2.to_streamlit(height=300)

# --- القسم الثاني: إعدادات الربط ---
if gdf1 is not None and gdf2 is not None:
    st.sidebar.title("⚙️ خيارات الربet")
    mode = st.sidebar.radio("نوع العملية:", ["Spatial Join (مكانى)", "Attribute Join (وصفى)"])
    
    final_gdf = None

    if mode == "Spatial Join (مكانى)":
        st.sidebar.subheader("إعدادات الربط المكاني")
        op = st.sidebar.selectbox("العلاقة:", ["intersects", "contains", "within", "touches"])
        if st.sidebar.button("تنفيذ الربط المكاني"):
            with st.spinner("جاري المعالجة..."):
                # توحيد نظام الإحداثيات ضروري جداً
                gdf2 = gdf2.to_crs(gdf1.crs)
                final_gdf = gpd.sjoin(gdf1, gdf2, how="left", predicate=op)

    else:
        st.sidebar.subheader("إعدادات الربط الوصفي")
        left_on = st.sidebar.selectbox("حقل الربط (Left):", gdf1.columns)
        right_on = st.sidebar.selectbox("حقل الربط (Right):", gdf2.columns)
        how = st.sidebar.selectbox("نوع الربط:", ["left", "inner", "outer"])
        if st.sidebar.button("تنفيذ الربط الوصفي"):
            with st.spinner("جاري الدمج..."):
                final_gdf = gdf1.merge(gdf2, left_on=left_on, right_on=right_on, how=how)

    # --- القسم الثالث: النتائج ---
    if final_gdf is not None:
        st.markdown("---")
        st.subheader("📊 نتيجة العملية")
        st.write(f"عدد السجلات الناتجة: {len(final_gdf)}")
        
        if len(final_gdf) == 0:
            st.warning("لا توجد نتائج متطابقة!")
        else:
            st.success("تم الربط بنجاح!")
            st.dataframe(final_gdf.head(10))
            
            # التحميل بصيغة GeoJSON كما هو مطلوب
            geojson_str = final_gdf.to_json()
            st.download_button(
                label="📥 تحميل النتيجة بصيغة GeoJSON",
                data=geojson_str,
                file_name="result_data.geojson",
                mime="application/json"
            )
else:
    st.info("💡 يرجى رفع الملفين لبدء عملية الربط.")