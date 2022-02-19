import sys,os
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal
gdal.UseExceptions() #允许捕获错误信息


inputRaster = "C:/data/coursedata/RS3915019025/chapter3/ZY320190629_Clip.tif"
outputRaster = "C:/data/coursedata/RS3915019025/chapter3/ZY320190629_Clip_8bits_maxmin.tif"
nodata=65535 # 标记nodata，以免将nodata作为最大值

try:
    srcRaster = gdal.Open(inputRaster)
except:
    print("Opening file failed:{}".format(inputRaster))
    sys.exit(-1)

height = srcRaster.RasterYSize
width = srcRaster.RasterXSize
im_bands = srcRaster.RasterCount
#获取输入影像的几何变换信息和坐标系信息
projinf = srcRaster.GetProjectionRef()
print(projinf)
geotransform = srcRaster.GetGeoTransform()
print(geotransform)

result = [] #空list，用于存储8bit数组
for bandId in range(srcRaster.RasterCount):
    bandId = bandId + 1
    band = srcRaster.GetRasterBand(bandId)
    band.SetNoDataValue(nodata) #根据事先指定的nodata值（65535），将波段图像中等于65535的数据标记为nodata

    print('原始波段元信息：{}\n'.format(band.GetMetadata()))
    bmin = band.GetMinimum()
    bmax = band.GetMaximum()
    # 如果元信息中没有最大最小值，需重新统计元信息
    if bmin is None or bmax is None:
        # (bmin, bmax) = band.ComputeRasterMinMax(1)
        band.ComputeStatistics(0)
        print('统计计算后，波段元信息：{}\n'.format(band.GetMetadata()))
        bmin = band.GetMinimum()
        bmax = band.GetMaximum()

    band_arr_tmp = band.ReadAsArray()
    if band_arr_tmp is None:
        print("load image failed")
        sys.exit(-2)

    index = np.where(band_arr_tmp == nodata) #查找nodata的位置，如果没有，返回空数组
    new_data = np.asarray(band_arr_tmp, dtype=np.float32) #数据变换成浮点型，np.nanargmin()函数要求输入浮点型
    if len(index) <2:
        print("no nodata")
        bmin = new_data.min()
        bmax =new_data.max()
    else:
        new_data[index] = np.nan
        t_min = np.nanargmin(new_data) #最小值的位置
        t_max =np.nanargmax(new_data) #最大值的位置
        bmin= (new_data.flatten())[t_min] #根据位置，查找图像最小值
        bmax =(new_data.flatten())[t_max]

    if bmin <0.00:
        bmin =0.00
    temp = 255.0 * (new_data - bmin) / (bmax - bmin + 0.000001)
    temp[temp < 0.00001] = 0
    temp[temp > 255.00001] = 255
    temp = np.asarray(temp, np.uint8)
    temp[index] = 255
    result.append(temp)
    plt.imshow(temp, cmap=plt.cm.gray)
    plt.show()

# 存储图像
driver = gdal.GetDriverByName("GTiff")
outdataset = driver.Create(outputRaster, width, height, im_bands, gdal.GDT_Byte)
outdataset.SetGeoTransform(geotransform) #添加几何变换信息
outdataset.SetProjection(projinf) #添加投影信息
for i in range(im_bands):
    outdataset.GetRasterBand(i + 1).WriteArray(result[i])
del outdataset
