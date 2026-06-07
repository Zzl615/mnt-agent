import os
from PIL import Image

def split_long_image(input_path, segment_height=2500, quality=95):
    """
    将长截图切分为多段
    :param input_path: 输入图片路径
    :param segment_height: 每段的目标高度（像素）
    :param quality: 输出图片质量 (1-100)
    """
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件: {input_path}")
        return

    # 打开图片
    img = Image.open(input_path)
    width, height = img.size
    print(f"📏 原始尺寸: {width}x{height}")

    # 创建输出目录
    dir_name = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.join(dir_name, f"{base_name}_segments")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 计算切分段数
    num_segments = (height + segment_height - 1) // segment_height
    
    for i in range(num_segments):
        top = i * segment_height
        # 确保最后一段高度准确
        bottom = min((i + 1) * segment_height, height)
        
        # 裁剪区域 (left, top, right, bottom)
        segment = img.crop((0, top, width, bottom))
        
        # 构建输出文件名
        output_filename = f"{base_name}_{i+1:02d}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        # 高清保存设置：
        # subsampling=0 禁用色彩子采样，保留边缘细节（对文字截图非常重要）
        segment.save(output_path, "JPEG", quality=quality, subsampling=0)
        print(f"✅ 已保存第 {i+1}/{num_segments} 段: {output_filename}")

    print(f"\n✨ 处理完成！切片保存在目录: {output_dir}")

if __name__ == "__main__":
    # 指定你的图片路径
    target_image = "/Users/noaghzil/Desktop/Phone-视频制作/Screenshot_2026-06-07-18-50-04-24.jpg"
    
    # 执行切分 (建议每段高度设为 2500 左右，适合手机阅读且方便管理)
    split_long_image(target_image, segment_height=2500)
