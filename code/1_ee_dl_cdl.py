import pandas as pd
import ee

ee.Initialize()

sample_reg = pd.read_pickle("../processed_data/sample_region.pkl")
sample_reg['eeGeom'] = sample_reg['coords'].apply(ee.Geometry.Polygon)
sample_reg['eeFeat'] = sample_reg['eeGeom'].apply(ee.Feature)

ee_sample_reg = ee.FeatureCollection(sample_reg['eeFeat'].tolist())

def cultivated(img):
    lt58 = img.lt(58)
    gt65 = img.gt(65)
    cult = lt58.Or(gt65)

    lt81 = img.lt(81)
    gt195 = img.gt(195)
    cult2 = lt81.Or(gt195)
    cult = cult.And(cult2)
    return(cult.rename("cultivated"))

def dl_cdl(year):
    # https://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL#bands
    cdl = ee.ImageCollection("USDA/NASS/CDL").filterDate(f"{year}-01-01",f"{year}-12-31").filterBounds(ee_sample_reg.geometry()).first() # Should only be one
    cdl = cdl.clip(ee_sample_reg.geometry())

    cdl_cult = cultivated(cdl.select("cropland"))
    cdl=cdl.select("cropland").addBands(cdl_cult)

    task = ee.batch.Export.image.toDrive(cdl,
            description=f"cdl_{year}",
            scale=30,
            crs= 'EPSG:3310',
            folder="sv_sjv_cdl",
            maxPixels=351000000)
    task.start()

for year in range(2009,2023):
    dl_cdl(year)
