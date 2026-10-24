// Observation compatibility only. No algorithm, portfolio, signal, brokerage or order API.
using System.Globalization;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using QuantConnect;
using QuantConnect.Data.Market;

static class Program
{
    static decimal Number(JToken x) => decimal.Parse((string)x!,CultureInfo.InvariantCulture);
    static string Num(decimal x) => x.ToString("G29",CultureInfo.InvariantCulture);
    static DateTime Clock(long ns) => DateTime.UnixEpoch.AddTicks(checked(ns+99)/100);
    static long Ns(DateTime t) => checked((t.Ticks-DateTime.UnixEpoch.Ticks)*100);
    static void Main(string[] args)
    {
        if(args.Length!=2 || File.Exists(args[1]))throw new InvalidOperationException("New private output required");
        var input=JObject.Parse(File.ReadAllText(args[0]));
        if((string)input["scope"]! !="PRIVATE_OBSERVATION_COMPATIBILITY_ONLY" ||
           (string)input["provider"]! !="alpaca" || (string)input["feed"]! !="sip" ||
           (string)input["status"]! !="UNQUALIFIED" || (bool)input["orders_enabled"]! ||
           (bool)input["historical_receipt_proven"]! || (string)input["symbol"]! !="SPY")
            throw new InvalidOperationException("Observation scope only");
        // Artificial diagnostic alias; NOT a historical class/listing identity.
        var symbol=new Symbol(SecurityIdentifier.GenerateEquity(new DateTime(2025,1,15),"SIPSPY",Market.USA),"SPY");
        var bars=new JArray();var quotes=new JArray();
        foreach(var row in (JArray)input["bars"]!)
        {
            var source=(long)row["source_ns"]!;
            var bar=new TradeBar(Clock(source),symbol,Number(row["open"]!),Number(row["high"]!),Number(row["low"]!),Number(row["close"]!),Number(row["volume"]!),TimeSpan.FromMinutes(1));
            bars.Add(new JObject{["source_ns"]=source,["native_ns"]=Ns(bar.Time),["native_end_ns"]=Ns(bar.EndTime),["open"]=Num(bar.Open),["high"]=Num(bar.High),["low"]=Num(bar.Low),["close"]=Num(bar.Close),["volume"]=Num(bar.Volume)});
        }
        foreach(var row in (JArray)input["quotes"]!)
        {
            var source=(long)row["source_ns"]!;
            // Size values retained in provider units; no capacity/share-unit claim.
            var tick=new Tick{Symbol=symbol,Time=Clock(source),TickType=TickType.Quote,BidPrice=Number(row["bid"]!),AskPrice=Number(row["ask"]!),BidSize=Number(row["bid_size"]!),AskSize=Number(row["ask_size"]!)};
            quotes.Add(new JObject{["source_ns"]=source,["native_ns"]=Ns(tick.Time),["bid"]=Num(tick.BidPrice),["ask"]=Num(tick.AskPrice),["bid_size"]=Num(tick.BidSize),["ask_size"]=Num(tick.AskSize),["same_time_variants"]=row["same_time_variants"]!.DeepClone()});
        }
        var output=new JObject{["scope"]="NATIVE_DATA_TYPE_ROUNDTRIP_ONLY",["orders"]=0,["historical_identity_admitted"]=false,["historical_receipt_proven"]=false,["bars"]=bars,["quotes"]=quotes};
        using var file=new FileStream(args[1],FileMode.CreateNew,FileAccess.Write,FileShare.None);
        using var writer=new StreamWriter(file);writer.Write(output.ToString(Formatting.None)+"\n");
    }
}
