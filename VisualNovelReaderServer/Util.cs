using Microsoft.CodeAnalysis.CSharp.Syntax;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace VisualNovelReaderServer
{
    public static class TimeExtensions
    {
        public static long ToUnixTimeMilliseconds(this DateTime time)
        {
            try
            {
                return new DateTimeOffset(time).ToUnixTimeMilliseconds();
            }
            catch (Exception)
            {

                return 0;
            }
        }

        public static long ToUnixTimeSeconds(this DateTime time)
        {
            try
            {
                return new DateTimeOffset(time).ToUnixTimeSeconds();
            }
            catch (Exception)
            {
                return 0;
            }
        }
    }

    public class Util
    {
        public static DateTime TimestampToDateTime(long seconds)
        {
            return DateTimeOffset.FromUnixTimeSeconds(seconds).UtcDateTime;
        }
    }
}
