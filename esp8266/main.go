package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/joho/godotenv"
	lark "github.com/larksuite/oapi-sdk-go/v3"
	larkcore "github.com/larksuite/oapi-sdk-go/v3/core"
	larkbitable "github.com/larksuite/oapi-sdk-go/v3/service/bitable/v1"
)

var (
	APP_ID     string
	APP_SECRET string
	client     *lark.Client
	now        = time.Now().Format("20060102-150405")
	// lastHour      = fmt.Sprintf("%d", time.Now().Hour()-1)
	yesterdatHour = time.Now().AddDate(0, 0, -1).Format("2006/01/02 15:") + "00:00"
)

func init() {
	cwd, _ := os.Getwd()
	fmt.Println("WorkDIR: ", cwd)
	fmt.Println("Load ENV From: ", os.Args[1:])
	godotenv.Load(os.Args[1:]...)
	APP_ID = os.Getenv("APP_ID")
	APP_SECRET = os.Getenv("APP_SECRET")
	client = lark.NewClient(APP_ID, APP_SECRET)
}

// AverageCalculator 结构体用于保存当前平均值和计数器
type AverageCalculator struct {
	Average float32
	Count   int
}

// Add 添加一个新的数据点并更新平均值
func (ac *AverageCalculator) Add(x float32) {
	ac.Count++
	if ac.Count == 1 {
		ac.Average = x
	} else {
		ac.Average = (float32(ac.Count-1)*ac.Average + x) / float32(ac.Count)
	}
}

type Fields struct {
	Temp float32 `json:"温度"`
	Huim float32 `json:"湿度"`
	Dp   float32 `json:"露点"`
	Day  struct {
		Type  int `json:"type"`
		Value []struct {
			Text string `json:"text"`
			// Type any    `json:"type"`
		} `json:"value"`
	} `json:"日期"`
	Hour struct {
		Type  int   `json:"type"`
		Value []int `json:"value"`
	} `json:"小时"`
}

func FieldsBuilder(rec map[string]interface{}) (Fields, error) {
	stRec := Fields{}
	jr, err := json.Marshal(rec)
	if err != nil {
		return stRec, err
	}
	err = json.Unmarshal(jr, &stRec)
	if err != nil {
		return stRec, err
	}
	return stRec, nil
}

// 保存一个小时的平均温湿度信息和输出的记录ID
type HourRecordAverage struct {
	Temp      AverageCalculator
	Huim      AverageCalculator
	Dp        AverageCalculator
	recordIds []string
}

// 向结构体中添加信息
func (hr *HourRecordAverage) Add(temp, huim, dp float32) {
	hr.Temp.Add(temp)
	hr.Huim.Add(huim)
	hr.Dp.Add(dp)
}

// 查询记录 一次最多500条
func search() ([]*larkbitable.AppTableRecord, error) {
	// 创建请求对象
	layout := "2006/01/02 15:00:00"
	yesterday := time.Now().AddDate(0, 0, -1).Format(layout)
	yesterday_time, _ := time.Parse(layout, yesterday)
	yesterday_tmp := yesterday_time.Unix()
	fmt.Printf("查找%s之前的数据.[%d]\n", yesterday, yesterday_tmp)
	req := larkbitable.NewSearchAppTableRecordReqBuilder().
		AppToken(`Ph6abuijPa0OySs2FdRcNZ92nyb`).
		TableId(`tblFkKvJ3oz7Bwyc`).
		PageSize(1450).
		Body(larkbitable.NewSearchAppTableRecordReqBodyBuilder().
			ViewId(`vewlYxeGPA`).
			FieldNames([]string{`日期`, `小时`, `温度`, `湿度`, `露点`, `时间戳`}).
			Sort([]*larkbitable.Sort{
				larkbitable.NewSortBuilder().
					FieldName(`时间戳`).
					Desc(false).
					Build(),
			}).
			Filter(larkbitable.NewFilterInfoBuilder().
				Conjunction(`and`).
				Conditions([]*larkbitable.Condition{
					larkbitable.NewConditionBuilder().
						FieldName(`时间戳`).
						Operator(`isLess`).
						Value([]string{yesterdatHour}).
						Build(),
				}).
				Build()).
			AutomaticFields(false).
			Build()).
		Build()
	// 发起请求
	resp, err := client.Bitable.V1.AppTableRecord.Search(context.Background(), req)
	// 处理错误
	if err != nil {
		fmt.Println(err)
		return make([]*larkbitable.AppTableRecord, 0), err
	}
	// 服务端错误处理
	if !resp.Success() {
		fmt.Printf("logId: %s, error response: \n%s", resp.RequestId(), larkcore.Prettify(resp.CodeError))
		return make([]*larkbitable.AppTableRecord, 0), err
	}
	// 业务处理
	os.WriteFile("SearchCache.json", resp.RawBody, 0x777)
	fmt.Printf("查询到 [%d] 条记录.\n", *resp.Data.Total)
	return resp.Data.Items, nil
}

// 批量删除记录，一次最多500条
func deleteRecord(recordIds []string) error {
	req := larkbitable.NewBatchDeleteAppTableRecordReqBuilder().
		AppToken(`Ph6abuijPa0OySs2FdRcNZ92nyb`).
		TableId(`tblFkKvJ3oz7Bwyc`).
		Body(
			larkbitable.NewBatchDeleteAppTableRecordReqBodyBuilder().Records(
				recordIds,
			).Build(),
		).Build()
	resp, err := client.Bitable.AppTableRecord.BatchDelete(context.Background(), req)
	if err != nil {
		fmt.Println(err)
		return err
	}
	// 服务端错误处理
	if !resp.Success() {
		fmt.Printf("logId: %s, error response: \n%s", resp.RequestId(), larkcore.Prettify(resp.CodeError))
		return err
	}
	// 业务处理
	os.Rename("SearchCache.json", fmt.Sprintf("SearchBackup_%s.json", now))
	fmt.Printf("删除了 [%d] 条数据", len(resp.Data.Records))
	return nil
}

// 向时均温度表中添加记录
func AddHourAvg(date string, te, hi, dp float32) error {
	_client := http.Client{}
	//https://mvawcxui6v5.feishu.cn/share/base/form/shrcnSOux7ctqyDxuWMLVuAIhcf
	st, err := time.Parse("2006/01/03 15:04:05", date)
	if err != nil {
		return err
	}
	_body := fmt.Sprintf(`{"shareToken":"shrcnSOux7ctqyDxuWMLVuAIhcf",
	"data":"{\"fldEi2LGAn\":{\"type\":5,\"value\":%d},\"fldF9Zuv8h\":{\"type\":2,\"value\":%.2f},\"fldcJbXiZR\":{\"type\":2,\"value\":%.2f},\"flduGPSBiZ\":{\"type\":2,\"value\":%.2f}}",
	"preUploadEnable":false}`, st.UnixMilli(), te, hi, dp)
	// fmt.Println(_body)
	// panic("Exit")
	req, err := http.NewRequest(
		"POST",
		"https://mvawcxui6v5.feishu.cn/space/api/bitable/share/content",
		bytes.NewBufferString(_body),
	)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Cookies", "session=U7CK1RF-405ld771-08cf-4d80-b3b4-0387ced795e8-NN5W4; _csrf_token=47424c6743a5873d3a11d77c3a0697fcfb1be058-1741437016;")
	req.Header.Set("x-csrftoken", "47424c6743a5873d3a11d77c3a0697fcfb1be058-1741437016")
	req.Header.Set("x-auth-token", "U7CK1RF-405ld771-08cf-4d80-b3b4-0387ced795e8-NN5W4")
	req.Header.Set("referer", "https://mvawcxui6v5.feishu.cn/share/base/form/shrcnSOux7ctqyDxuWMLVuAIhcf")
	resp, err := _client.Do(req)
	if err != nil {
		return err
	}
	respBody, err := io.ReadAll(resp.Body)
	defer resp.Body.Close()
	if resp.StatusCode == 200 {
		fmt.Printf("Add Hour Agv Success. [%s] T: %.2f  H: %.2f  D:%.2f\n", date, te, hi, dp)
		fmt.Printf("%s\n", respBody)
		return nil
	}
	if err != nil {
		return fmt.Errorf("error reading response body: %s", err)
	}
	return fmt.Errorf("add hour avg error [%d] %s", resp.StatusCode, respBody)
}
func main() {
	records, err := search()
	if err != nil {
		fmt.Println(err)
		return
	}
	_ = records
	rest := make(map[string]*HourRecordAverage, 0)
	dels := make([]string, 0)
	// // fmt.Println(records)
	for _, rec := range records {
		fds, err := FieldsBuilder(rec.Fields)
		if err != nil {
			fmt.Println(err)
		}
		if len(fds.Day.Value) == 0 {
			panic(fmt.Errorf("record[%s] .Day of range with length 0", *rec.RecordId))
		}
		if len(fds.Hour.Value) == 0 {
			panic(fmt.Errorf("record[%s] .Hour of range with length 0", *rec.RecordId))
		}
		key := fds.Day.Value[0].Text + " " + fmt.Sprintf("%d", fds.Hour.Value[0]) + ":00:00"
		_, exsit := rest[key]
		if !exsit {
			rest[key] = &HourRecordAverage{
				recordIds: make([]string, 0),
			}
		}
		rest[key].Add(fds.Temp, fds.Huim, fds.Dp)
		rest[key].recordIds = append(rest[key].recordIds, *rec.RecordId)
	}
	// fmt.Println(rest)
	// larkcore.Prettify(rest)
	for k, v := range rest {
		err := AddHourAvg(k, v.Temp.Average, v.Huim.Average, v.Dp.Average)
		if err == nil {
			dels = append(dels, v.recordIds...)
		} else {
			fmt.Println(err)
		}
		time.Sleep(1 * time.Second)
	}
	fmt.Println("Deletes:", len(dels), dels)
	if len(dels) == 0 {
		return
	}

	_err := deleteRecord(dels)
	if _err != nil {
		fmt.Println(err)
	}
}
