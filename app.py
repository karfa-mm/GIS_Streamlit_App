import streamlit as st
import geopandas as gpd
import pandas as pd
import leafmap.foliumap as leafmap
import os
import zipfile
import tempfile

# إعدادات الصفحة
st.set_page_config(layout="wide", page_title="GIS Spatial & Attribute Join Tool")

# --- الواجهة الجانبية (Sidebar) ---
st.sidebar.title("🛠️ لوحة التحكم")
st.sidebar.info("استخدم هذه اللوحة لاختيار نوع الربط والإعدادات.")

st.title("🌐 تطبيق معالجة البيانات الجغرافية (GIS)")

# وظيفة معالجة الملفات المرفوعة
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                name = uploaded_file.name
                if name.endswith('.zip'):
                    with zipfile.ZipFile(uploaded_file, 'r') as z:
                        z.extractall(tmpdir)
                    for r, d, files in os.walk(tmpdir):
                        for f in files:
                            if f.endswith('.shp'):
                                return gpd.read_file(os.path.join(r, f))
                elif name.endswith('.geojson'):
                    return gpd.read_file(uploaded_file)
                else:
                    st.error(f"الصيغة {name} غير مدعومة!")
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")
    return None

# --- أولاً: رفع الملفات ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 الملف الأساسي (Left)")
    file_l = st.file_uploader("ارفع ZIP أو GeoJSON", key="left_file")
    gdf_l = load_data(file_l)
    if gdf_l is not None:
        st.write("أول 5 صفوف:")
        st.dataframe(gdf_l.head(5))
        m1 = leafmap.Map(draw_control=False)
        m1.add_gdf(gdf_l, layer_name="Base Layer")
        m1.to_streamlit(height=300)

with col2:
    st.subheader("📁 الملف الثانوي (Right)")
    file_r = st.file_uploader("ارفع ZIP أو GeoJSON", key="right_file")
    gdf_r = load_data(file_r)
    if gdf_r is not None:
        st.write("أول 5 صفوف:")
        st.dataframe(gdf_r.head(5))
        m2 = leafmap.Map(draw_control=False)
        m2.add_gdf(gdf_r, layer_name="Join Layer")
        m2.to_streamlit(height=300)

# --- ثانياً: إعدادات الربط ---
if gdf_l is not None and gdf_r is not None:
    st.sidebar.divider()
    join_mode = st.sidebar.radio("اختر نوع الربط:", ["ربط مكاني (Spatial Join)", "ربط وصفي (Attribute Join)"])
    
    result = None
    
    if join_mode == "ربط مكاني (Spatial Join)":
        st.sidebar.subheader("إعدادات الربط المكاني")
        predicate = st.sidebar.selectbox("العلاقة المكانية:", ["intersects", "contains", "within", "touches", "overlaps"])
        
        if st.sidebar.button("تنفيذ الربط المكاني 🚀"):
            with st.spinner('جاري معالجة البيانات مكانياً...'):
                gdf_r = gdf_r.to_crs(gdf_l.crs)
                result = gpd.sjoin(gdf_l, gdf_r, how="left", predicate=predicate)

    else:
        st.sidebar.subheader("إعدادات الربط الوصفي")
        left_key = st.sidebar.selectbox("حقل الربط من الملف الأساسي:", gdf_l.columns)
        right_key = st.sidebar.selectbox("حقل الربط من الملف الثانوي:", gdf_r.columns)
        how_join = st.sidebar.selectbox("نوع Join:", ["left", "right", "inner", "outer"])
        
        if st.sidebar.button("تنفيذ الربط الوصفي 🚀"):
            with st.spinner('جاري ربط الجداول...'):
                result = gdf_l.merge(gdf_r, left_on=left_key, right_on=right_key, how=how_join)

    # --- ثالثاً ورابعاً: عرض النتائج وتنزيلها ---
    if result is not None:
        st.divider()
        st.header("📊 النتائج")
        st.write(f"عدد الأسطر الناتجة: **{len(result)}**")
        
        if len(result) == 0:
            st.warning("⚠️ لا توجد نتائج مطابقة بناءً على الإعدادات المختارة.")
        else:
            st.success("تمت العملية بنجاح!")
            st.dataframe(result.head(10))
            
            # تحويل النتيجة لـ GeoJSON للتنزيل
            try:
                geojson_data = result.to_json()
                st.download_button(
                    label="📥 تنزيل النتائج بصيغة GeoJSON",
                    data=geojson_data,
                    file_name="joined_data.geojson",
                    mime="application/json"
                )
            except:
                st.error("فشل تحويل البيانات لـ GeoJSON. تأكد من وجود أعمدة جغرافية صحيحة.")