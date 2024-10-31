import xlwt
import xlrd
import subprocess


if __name__ == '__main__':
# 创建一个新的Excel工作簿
    workbook = xlwt.Workbook(encoding='utf-8')
    sheet = workbook.add_sheet('Sheet1')

    # 设置表头
    headers = ["代价", "容量限制"]
    for col_num, header in enumerate(headers):
        sheet.write(0, col_num, header)

    # 运行项目1000次并将结果保存到Excel表格
    for i in range(1, 101):
        # 运行项目
        subprocess.run(["python", "main.py"])

        # 将结果保存到Excel表格中
        workbook_read = xlrd.open_workbook(r'C:\Users\Lenovo\Desktop\mp_new_new.xlsx')
        # 选择要读取的工作表
        worksheet_read = workbook_read.sheet_by_index(0)
        for row in range(worksheet_read.nrows):
            for col in range(worksheet_read.ncols):
                value = worksheet_read.cell_value(row, col)
                sheet.write(row + i, col, value)

    # 保存Excel表格
    workbook.save(r'C:\Users\Lenovo\Desktop\mp_new_new_result_3.xlsx')
